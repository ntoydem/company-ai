import io
import json
import uuid
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.document import Confidentiality, Document, IngestionStatus
from app.models.document_metadata_suggestion import DocumentMetadataSuggestion, SuggestionStatus
from app.models.ingestion_job import IngestionJob, IngestionJobStatus
from app.models.project import Project
from app.models.user import User
from app.repositories import document_metadata_suggestion_repo
from app.services.document_store import LocalFileSystemStore
from tests.department_fixtures import add_user_to_department, make_department
from tests.fakes import FakeLLMClient

FAKE_PDF = b"%PDF-1.4\n%fake-pdf-for-tests\n1 0 obj\n<< >>\nendobj\ntrailer\n<< >>\n%%EOF"


def _document(
    session: Session,
    *,
    department: str | None = None,
    confidentiality: Confidentiality = Confidentiality.normal,
) -> Document:
    """A `Document` row created directly — shorter than a real `/upload` call for tests
    that only care about authorization, not the upload endpoint itself (`/upload` accepts
    `department`/`confidentiality` too since Phase 3.2, see `_upload`)."""
    document = Document(
        title="t",
        document_type="dt",
        counterparty="c",
        document_date=date(2023, 1, 1),
        storage_path=f"{uuid.uuid4()}/original.pdf",
        department=department,
        confidentiality=confidentiality,
    )
    session.add(document)
    session.commit()
    return document


def _document_with_file(
    session: Session,
    settings: Settings,
    *,
    department: str | None,
    confidentiality: Confidentiality = Confidentiality.normal,
) -> Document:
    """Like `_document`, but also writes a real file to disk so `/download` succeeds."""
    document_id = uuid.uuid4()
    store = LocalFileSystemStore(settings.documents_dir)
    stored = store.store(document_id, "original.pdf", io.BytesIO(FAKE_PDF))
    document = Document(
        id=document_id,
        title="t",
        document_type="dt",
        counterparty="c",
        document_date=date(2023, 1, 1),
        storage_path=str(stored.original_path.relative_to(settings.documents_dir)),
        department=department,
        confidentiality=confidentiality,
    )
    session.add(document)
    session.commit()
    return document


def _upload(
    client: TestClient,
    *,
    filename: str = "facility_agreement.pdf",
    content: bytes = FAKE_PDF,
    content_type: str = "application/pdf",
    title: str = "Facility Agreement",
    document_type: str = "facility_agreement",
    document_date: str = "2023-06-01",
    counterparty: str = "PQR Bank",
    **extra: str,
):
    return client.post(
        "/api/documents/upload",
        files={"file": (filename, content, content_type)},
        data={
            "title": title,
            "document_type": document_type,
            "document_date": document_date,
            "counterparty": counterparty,
            **extra,
        },
    )


def test_upload_creates_document_and_job_row(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    response = _upload(client)
    assert response.status_code == 201
    body = response.json()
    assert body["ingestion_status"] == "uploaded"
    document_id = uuid.UUID(body["id"])

    document = db_session.get(Document, document_id)
    assert document is not None
    assert document.title == "Facility Agreement"
    assert document.uploaded_by_id == admin_user.id
    # Not sent in this particular request — `department`/`project_id` stay their defaults.
    assert document.department is None
    assert document.project_id is None
    assert document.confidentiality.value == "normal"

    job = db_session.scalar(select(IngestionJob).where(IngestionJob.document_id == document_id))
    assert job is not None
    assert job.status == IngestionJobStatus.queued
    assert job.attempts == 0


def test_upload_missing_required_field_returns_422(client: TestClient, admin_user: User) -> None:
    response = client.post(
        "/api/documents/upload",
        files={"file": ("f.pdf", FAKE_PDF, "application/pdf")},
        data={"document_type": "facility_agreement", "document_date": "2023-06-01"},
    )
    assert response.status_code == 422


def test_upload_exe_rejected_with_415(client: TestClient, admin_user: User) -> None:
    response = _upload(
        client,
        filename="virus.exe",
        content=b"MZ\x90\x00not-a-real-exe",
        content_type="application/octet-stream",
    )
    assert response.status_code == 415


def test_upload_corrupt_but_pdf_shaped_file_is_accepted_at_upload_time(
    client: TestClient, admin_user: User
) -> None:
    """A truncated/malformed PDF still has a valid `%PDF-` header, so upload succeeds —
    the corruption is only caught by ocr-worker's pipeline (kabul kriteri 3a)."""
    response = _upload(client, content=b"%PDF-1.4\nthis is not a real pdf body")
    assert response.status_code == 201


def test_list_documents_returns_uploaded_document(client: TestClient, admin_user: User) -> None:
    upload_response = _upload(client)
    document_id = upload_response.json()["id"]

    response = client.get("/api/documents")
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert document_id in ids


def test_get_document_status_returns_fields(client: TestClient, admin_user: User) -> None:
    document_id = _upload(client).json()["id"]

    response = client.get(f"/api/documents/{document_id}/status")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == document_id
    assert body["ingestion_status"] == "uploaded"
    assert body["ingestion_error"] is None
    assert body["page_count"] is None


def test_get_document_status_404_for_unknown_id(client: TestClient, admin_user: User) -> None:
    response = client.get(f"/api/documents/{uuid.uuid4()}/status")
    assert response.status_code == 404


def test_upload_with_supersedes_links_the_chain(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    facility = _upload(client, status="executed", effective_date="2023-06-01").json()
    facility_id = uuid.UUID(facility["id"])
    response = _upload(
        client,
        title="Amendment 01",
        document_date="2025-03-15",
        status="executed",
        effective_date="2025-03-15",
        version="1",
        supersedes_document_id=str(facility_id),
    )
    assert response.status_code == 201
    amendment = db_session.get(Document, uuid.UUID(response.json()["id"]))
    facility = db_session.get(Document, facility_id)
    assert amendment is not None and facility is not None
    assert amendment.supersedes_document_id == facility_id
    assert amendment.effective_date == date(2025, 3, 15)
    assert facility.superseded_by_document_id == amendment.id
    assert facility.status.value == "superseded"  # Phase 3.2: mark_superseded now transitions this


def test_upload_supersedes_already_superseded_is_409(client: TestClient, admin_user: User) -> None:
    facility_id = _upload(client).json()["id"]
    assert _upload(client, title="Amd 1", supersedes_document_id=facility_id).status_code == 201
    response = _upload(client, title="Amd 1 again", supersedes_document_id=facility_id)
    assert response.status_code == 409
    assert response.json()["detail"] == "Belge zaten başka bir belge tarafından güncellenmiş."


def test_upload_supersedes_unknown_document_is_404(client: TestClient, admin_user: User) -> None:
    response = _upload(client, supersedes_document_id=str(uuid.uuid4()))
    assert response.status_code == 404


def test_upload_version_must_be_positive(client: TestClient, admin_user: User) -> None:
    assert _upload(client, version="0").status_code == 422


# --- Phase 3.2: upload form's department/project/confidentiality, AI metadata suggestion ---


def _classify_json(**overrides: object) -> str:
    fields = {
        "department": {"value": None, "confidence": 0.0},
        "subdepartment": {"value": None, "confidence": 0.0},
        "project_code": {"value": None, "confidence": 0.0},
        "document_type": {"value": "facility_agreement", "confidence": 0.8},
        "counterparty": {"value": "PQR Bank", "confidence": 0.8},
        "document_date": {"value": "2023-06-01", "confidence": 0.8},
        "status": {"value": "executed", "confidence": 0.8},
        "confidentiality": {"value": "normal", "confidence": 0.8},
        "tags": {"value": ["facility"], "confidence": 0.6},
    }
    fields.update(overrides)
    return json.dumps(fields)


def _make_project(session: Session, *, code: str = "ANK_RES") -> Project:
    project = Project(name=code, code=code)
    session.add(project)
    session.commit()
    return project


def test_upload_with_department_project_and_confidentiality(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    make_department(db_session, slug="finans")
    project = _make_project(db_session)

    response = _upload(
        client,
        department="finans",
        subdepartment="Muhasebe",
        project_id=str(project.id),
        confidentiality="restricted",
    )

    assert response.status_code == 201
    document = db_session.get(Document, uuid.UUID(response.json()["id"]))
    assert document is not None
    assert document.department == "finans"
    assert document.subdepartment == "Muhasebe"
    assert document.project_id == project.id
    assert document.confidentiality == Confidentiality.restricted


def test_upload_unknown_department_returns_422(client: TestClient, admin_user: User) -> None:
    response = _upload(client, department="hayali_departman")
    assert response.status_code == 422


def test_upload_unknown_project_id_returns_404(client: TestClient, admin_user: User) -> None:
    response = _upload(client, project_id=str(uuid.uuid4()))
    assert response.status_code == 404


def test_list_item_carries_subdepartment_and_confidentiality(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    """Phase 3.3: the Belgeler screen filters Enerji sub-cards by `subdepartment` and
    shows `confidentiality` — both were missing from the list item before."""
    document = _document(db_session, department="enerji_grubu")
    document.subdepartment = "Geliştirme"
    db_session.commit()

    item = next(i for i in client.get("/api/documents").json() if i["id"] == str(document.id))

    assert item["subdepartment"] == "Geliştirme"
    assert item["confidentiality"] == "normal"


def test_get_document_returns_full_metadata(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    """Phase 3.3 SORU 1: `GET /api/documents/{id}`."""
    facility_id = _upload(client, status="executed", effective_date="2023-06-01").json()["id"]
    amendment_id = _upload(
        client, title="Amendment 01", version="2", supersedes_document_id=facility_id
    ).json()["id"]

    response = client.get(f"/api/documents/{amendment_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Amendment 01"
    assert body["version"] == 2
    assert body["supersedes_document_id"] == facility_id
    assert body["tags"] == []
    assert body["ingestion_status"] == "uploaded"
    assert body["page_count"] is None
    facility = client.get(f"/api/documents/{facility_id}").json()
    assert facility["superseded_by_document_id"] == amendment_id
    assert facility["status"] == "superseded"


def test_get_document_hides_other_department_document_with_404(
    client: TestClient, db_session: Session, employee_user: User
) -> None:
    enerji = make_department(db_session, slug="enerji_grubu")
    add_user_to_department(db_session, employee_user, enerji)
    finans_doc = _document(db_session, department="finans")

    assert client.get(f"/api/documents/{finans_doc.id}").status_code == 404


def test_suggest_metadata_requires_admin(
    client: TestClient, db_session: Session, employee_user: User, fake_llm: FakeLLMClient
) -> None:
    document = _document(db_session)
    response = client.post(f"/api/documents/{document.id}/suggest-metadata")
    assert response.status_code == 403


def test_suggest_metadata_requires_ready_ingestion(
    client: TestClient, db_session: Session, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    document = _document(db_session)  # ingestion_status defaults to "uploaded"
    response = client.post(f"/api/documents/{document.id}/suggest-metadata")
    assert response.status_code == 409
    assert fake_llm.requests == []


def test_suggest_metadata_creates_suggestion_with_fields_and_confidence(
    client: TestClient, db_session: Session, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    document = _document(db_session)
    document.ingestion_status = IngestionStatus.ready
    db_session.commit()
    fake_llm.replies = [_classify_json(department={"value": None, "confidence": 0.0})]

    response = client.post(f"/api/documents/{document.id}/suggest-metadata")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"
    assert body["fields"]["document_type"] == {"value": "facility_agreement", "confidence": 0.8}
    assert body["document_id"] == str(document.id)


def test_suggest_metadata_is_idempotent_while_pending(
    client: TestClient, db_session: Session, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    document = _document(db_session)
    document.ingestion_status = IngestionStatus.ready
    db_session.commit()
    fake_llm.replies = [_classify_json()]

    first = client.post(f"/api/documents/{document.id}/suggest-metadata")
    second = client.post(f"/api/documents/{document.id}/suggest-metadata")

    assert first.status_code == second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert len(fake_llm.requests) == 1  # not reclassified — still `pending`


def test_suggest_metadata_regenerates_after_rejection(
    client: TestClient, db_session: Session, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    document = _document(db_session)
    document.ingestion_status = IngestionStatus.ready
    db_session.commit()
    fake_llm.replies = [_classify_json(), _classify_json()]

    client.post(f"/api/documents/{document.id}/suggest-metadata")
    client.post(f"/api/documents/{document.id}/metadata-suggestion/reject")
    client.post(f"/api/documents/{document.id}/suggest-metadata")

    assert len(fake_llm.requests) == 2


def test_get_metadata_suggestion_404_when_none(client: TestClient, admin_user: User) -> None:
    document_id = _upload(client).json()["id"]
    response = client.get(f"/api/documents/{document_id}/metadata-suggestion")
    assert response.status_code == 404


def test_get_metadata_suggestion_visible_to_non_admin_with_document_access(
    client: TestClient, db_session: Session, employee_user: User, fake_llm: FakeLLMClient
) -> None:
    """Viewing a suggestion is not admin-only — only accepting/rejecting one is
    (SORU 2, docs/plans/PHASE_3_2_PLAN.md)."""
    finans = make_department(db_session, slug="finans")
    add_user_to_department(db_session, employee_user, finans)
    document = _document(db_session, department="finans")
    document.ingestion_status = IngestionStatus.ready
    document_metadata_suggestion = _seed_suggestion(db_session, document.id)

    response = client.get(f"/api/documents/{document.id}/metadata-suggestion")

    assert response.status_code == 200
    assert response.json()["id"] == str(document_metadata_suggestion.id)


def _seed_suggestion(session: Session, document_id: uuid.UUID) -> DocumentMetadataSuggestion:
    suggestion = document_metadata_suggestion_repo.upsert(
        session,
        document_id=document_id,
        model="fake-model",
        status=SuggestionStatus.pending,
        fields={"department": {"value": "finans", "confidence": 0.9}},
    )
    session.commit()
    return suggestion


def test_apply_metadata_suggestion_requires_admin(
    client: TestClient, db_session: Session, employee_user: User
) -> None:
    document = _document(db_session)
    _seed_suggestion(db_session, document.id)
    response = client.post(
        f"/api/documents/{document.id}/metadata-suggestion/apply", json={"department": "finans"}
    )
    assert response.status_code == 403


def test_apply_metadata_suggestion_writes_only_given_fields(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    make_department(db_session, slug="finans")
    document = _document(db_session)
    original_type = document.document_type
    _seed_suggestion(db_session, document.id)

    response = client.post(
        f"/api/documents/{document.id}/metadata-suggestion/apply",
        json={"department": "finans", "confidentiality": "restricted"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["department"] == "finans"
    db_session.refresh(document)
    assert document.confidentiality == Confidentiality.restricted
    assert document.document_type == original_type  # untouched — not in the request body


def test_apply_metadata_suggestion_unknown_department_returns_422(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    document = _document(db_session)
    _seed_suggestion(db_session, document.id)
    response = client.post(
        f"/api/documents/{document.id}/metadata-suggestion/apply",
        json={"department": "hayali_departman"},
    )
    assert response.status_code == 422


def test_apply_metadata_suggestion_unknown_project_code_returns_404(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    document = _document(db_session)
    _seed_suggestion(db_session, document.id)
    response = client.post(
        f"/api/documents/{document.id}/metadata-suggestion/apply",
        json={"project_code": "HAYALI_PRJ"},
    )
    assert response.status_code == 404


def test_apply_metadata_suggestion_null_mandatory_field_returns_422(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    document = _document(db_session)
    _seed_suggestion(db_session, document.id)
    response = client.post(
        f"/api/documents/{document.id}/metadata-suggestion/apply",
        json={"confidentiality": None},
    )
    assert response.status_code == 422


def test_reject_metadata_suggestion_requires_admin(
    client: TestClient, db_session: Session, employee_user: User
) -> None:
    document = _document(db_session)
    _seed_suggestion(db_session, document.id)
    response = client.post(f"/api/documents/{document.id}/metadata-suggestion/reject")
    assert response.status_code == 403


def test_reject_metadata_suggestion_marks_rejected_and_leaves_document_untouched(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    document = _document(db_session)
    original_department = document.department
    _seed_suggestion(db_session, document.id)

    response = client.post(f"/api/documents/{document.id}/metadata-suggestion/reject")

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    db_session.refresh(document)
    assert document.department == original_department


# --- Phase 1.2: role + department membership + confidentiality rules (SPEC_02 §5) ---


def test_employee_list_excludes_other_department_documents(
    client: TestClient, db_session: Session, employee_user: User
) -> None:
    """Kabul kriteri 1: enerji → finans belgesi listede yok."""
    enerji = make_department(db_session, slug="enerji_grubu")
    add_user_to_department(db_session, employee_user, enerji)
    _document(db_session, department="finans")
    own_doc = _document(db_session, department="enerji_grubu")

    response = client.get("/api/documents")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [str(own_doc.id)]


def test_employee_download_other_department_document_returns_403(
    client: TestClient, db_session: Session, employee_user: User
) -> None:
    """Kabul kriteri 1: enerji → finans belgesini indiremez (403)."""
    enerji = make_department(db_session, slug="enerji_grubu")
    add_user_to_department(db_session, employee_user, enerji)
    finans_doc = _document(db_session, department="finans")

    response = client.get(f"/api/documents/{finans_doc.id}/download")

    assert response.status_code == 403


def test_finans_cannot_download_hukuk_document(
    client: TestClient, db_session: Session, employee_user: User
) -> None:
    """Kabul kriteri 2: finans → legal (hukuk) belgesi 403."""
    finans = make_department(db_session, slug="finans")
    add_user_to_department(db_session, employee_user, finans)
    hukuk_doc = _document(db_session, department="hukuk")

    response = client.get(f"/api/documents/{hukuk_doc.id}/download")

    assert response.status_code == 403


def test_finans_can_download_own_department_document(
    client: TestClient, db_session: Session, settings: Settings, employee_user: User
) -> None:
    """Kabul kriteri 2: finans → kendi belgesi 200."""
    finans = make_department(db_session, slug="finans")
    add_user_to_department(db_session, employee_user, finans)
    own_doc = _document_with_file(db_session, settings, department="finans")

    response = client.get(f"/api/documents/{own_doc.id}/download")

    assert response.status_code == 200


def test_management_can_download_any_department_and_confidentiality_level(
    client: TestClient, db_session: Session, settings: Settings, management_user: User
) -> None:
    """Kabul kriteri 2: yonetim → hepsi 200 (restricted dahil)."""
    doc = _document_with_file(
        db_session, settings, department="hukuk", confidentiality=Confidentiality.restricted
    )

    response = client.get(f"/api/documents/{doc.id}/download")

    assert response.status_code == 200


def test_employee_cannot_download_restricted_document_of_own_department(
    client: TestClient, db_session: Session, employee_user: User
) -> None:
    """Kabul kriteri 2: restricted/board kuralı — employee kendi departmanında bile
    restricted belgeyi göremez."""
    finans = make_department(db_session, slug="finans")
    add_user_to_department(db_session, employee_user, finans)
    restricted_doc = _document(
        db_session, department="finans", confidentiality=Confidentiality.restricted
    )

    response = client.get(f"/api/documents/{restricted_doc.id}/download")

    assert response.status_code == 403


def test_download_unknown_document_returns_403(client: TestClient, admin_user: User) -> None:
    """An id that doesn't exist is never in `allowed_document_ids`'s result either, so it
    is rejected by the same 403 check as a real document the caller can't see — the
    existence-hiding 404 branch below it is unreachable in practice, kept only as a
    defensive fallback."""
    response = client.get(f"/api/documents/{uuid.uuid4()}/download")
    assert response.status_code == 403
