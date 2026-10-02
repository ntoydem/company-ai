"""Idempotent demo document seed (Phase 3.1) — `ensure_demo_documents` against the real
generated manifest (`seed_data/documents/manifest.json`, from `generate_documents.py`)."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.document import Document
from app.models.ingestion_job import IngestionJob
from app.services.admin_seed import ensure_admin_user
from app.services.demo_departments_seed import ensure_demo_departments
from app.services.demo_documents_seed import ensure_demo_documents
from app.services.demo_projects_seed import ensure_demo_projects
from app.services.version_chain import evaluate_version_chains

MANIFEST_PATH = Path(__file__).resolve().parent.parent / "seed_data" / "documents" / "manifest.json"

_FACILITY_CHAIN = [
    "DOC-ANK-FIN-001",
    "DOC-ANK-FIN-002",
    "DOC-ANK-FIN-003",
    "DOC-ANK-FIN-004",
    "DOC-ANK-FIN-005",
    "DOC-ANK-FIN-006",
]  # Phase 5.1: V01/V02 (002/003) are now rendered too — the full 6-link chain, not just 4.


def _prepare(session: Session, settings: Settings) -> None:
    ensure_admin_user(session, settings)
    ensure_demo_departments(session, settings)
    ensure_demo_projects(session, settings)


def _seeded_documents(session: Session) -> dict[str, Document]:
    rows = session.scalars(select(Document).where(Document.external_ref.is_not(None))).all()
    return {d.external_ref: d for d in rows if d.external_ref is not None}


def test_seed_creates_70_pdfs_plus_4_workbooks_and_queues_pdf_jobs(
    db_session: Session, settings: Settings
) -> None:
    _prepare(db_session, settings)

    results = ensure_demo_documents(db_session, settings, MANIFEST_PATH)

    assert len(results) == 74  # 70 PDF (Phase 3.1 + 5.1) + 4 workbook (Phase 4.2)
    assert all(r.created for r in results)
    documents = _seeded_documents(db_session)
    assert len(documents) == 74
    workbooks = [d for d in documents.values() if d.storage_path.endswith(".xlsx")]
    assert len(workbooks) == 4 and all(d.ingestion_status.value == "ready" for d in workbooks)
    pdfs = [d for d in documents.values() if d.storage_path.endswith(".pdf")]
    assert len(pdfs) == 70 and all(d.ingestion_status.value == "uploaded" for d in pdfs)
    jobs = db_session.scalars(
        select(IngestionJob).where(IngestionJob.document_id.in_([d.id for d in documents.values()]))
    ).all()
    assert len(jobs) == 70  # workbooks get no OCR job
    assert all(j.status.value == "queued" for j in jobs)


def test_seed_is_idempotent(db_session: Session, settings: Settings) -> None:
    _prepare(db_session, settings)
    ensure_demo_documents(db_session, settings, MANIFEST_PATH)

    results = ensure_demo_documents(db_session, settings, MANIFEST_PATH)

    assert len(results) == 74  # 70 PDF (Phase 3.1 + 5.1) + 4 workbook (Phase 4.2)
    assert all(r.created is False for r in results)
    assert len(_seeded_documents(db_session)) == 74


def test_seeded_metadata_matches_ledger(db_session: Session, settings: Settings) -> None:
    _prepare(db_session, settings)
    ensure_demo_documents(db_session, settings, MANIFEST_PATH)
    documents = _seeded_documents(db_session)

    facility = documents["DOC-ANK-FIN-004"]
    assert facility.department == "finans"
    assert facility.confidentiality.value == "normal"
    assert facility.status.value == "superseded"
    assert facility.project_id is not None  # linked to Ankara RES

    board_resolution = documents["DOC-CO-ADM-001"]
    assert board_resolution.department == "idari_isler"
    assert board_resolution.confidentiality.value == "board"
    assert board_resolution.project_id is None  # company-level, not project-scoped


def test_facility_chain_is_linear_and_single_current(
    db_session: Session, settings: Settings
) -> None:
    _prepare(db_session, settings)
    ensure_demo_documents(db_session, settings, MANIFEST_PATH)
    documents = _seeded_documents(db_session)

    for earlier_ref, later_ref in zip(_FACILITY_CHAIN, _FACILITY_CHAIN[1:], strict=False):
        earlier, later = documents[earlier_ref], documents[later_ref]
        assert later.supersedes_document_id == earlier.id
        assert earlier.superseded_by_document_id == later.id

    positions = evaluate_version_chains(documents.values(), settings.demo_today)
    current_refs = [ref for ref in _FACILITY_CHAIN if positions[documents[ref].id].is_current]
    assert current_refs == ["DOC-ANK-FIN-006"]
    assert positions[documents["DOC-ANK-FIN-001"].id].is_initial is True


def test_licence_amendment_is_related_not_superseding(
    db_session: Session, settings: Settings
) -> None:
    """Kendi kararım (plan T1): lisans tadili lisansı `supersedes` etmez — ikisi de aynı
    anda geçerli (kapasite değişti, lisans yürürlükten kalkmadı); bağlantı `related`."""
    _prepare(db_session, settings)
    ensure_demo_documents(db_session, settings, MANIFEST_PATH)
    documents = _seeded_documents(db_session)

    licence, amendment = documents["DOC-ANK-DEV-001"], documents["DOC-ANK-DEV-002"]
    assert amendment.supersedes_document_id is None
    assert licence.superseded_by_document_id is None
    assert licence.id in amendment.related_document_ids


def test_seed_records_ledger_parties_as_extra_field(
    db_session: Session, settings: Settings
) -> None:
    """B-28b (Naci SORU 2): the ledger's `parties` become `extra_fields.parties` on seeded
    documents and workbooks; nothing else is written there."""
    _prepare(db_session, settings)
    ensure_demo_documents(db_session, settings, MANIFEST_PATH)
    docs = _seeded_documents(db_session)
    facility = docs["DOC-ANK-FIN-001"]
    assert facility.extra_fields["parties"]["source"] == "user"
    assert "PQR Bank" in facility.extra_fields["parties"]["value"]
    workbook = docs["DOC-ANK-FIN-009"]
    assert "PQR Bank" in workbook.extra_fields["parties"]["value"]
    assert set(facility.extra_fields) == {"parties"}
