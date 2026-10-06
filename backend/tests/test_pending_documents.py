"""Tansu Not 7 §3 (T7-3…T7-6) — "the answer may be in a document still processing", behind
ASSIST_MODE. No LLM for the pending check itself; the model never sees these documents;
every title comes from the same gate as `/api/documents` (G3)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.audit_log import AuditLog
from app.models.document import Document, DocumentReviewStatus, IngestionStatus
from app.models.document_chunk import DocumentChunk
from app.models.project import Project
from app.models.user import User
from app.services import ingestion_errors, pending_documents
from app.services.answer_prompt import NO_ANSWER_TEXT
from app.services.ask_router import DOCUMENT_PART_HEADING
from tests.department_fixtures import add_user_to_department, make_department
from tests.fakes import FakeLLMClient, FakeRouter
from tests.test_ask import _ask, _document

SENTINEL = "GIZLI-ISLENMEMIS-DEGER-7788"


@pytest.fixture
def assist_on(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "assist_mode_enabled", True)


def _pending(
    session: Session,
    *,
    title: str,
    department: str | None,
    ingestion_status: IngestionStatus = IngestionStatus.ocr,
    review_status: DocumentReviewStatus = DocumentReviewStatus.approved,
    ingestion_error: str | None = None,
    uploaded_by: User | None = None,
    days_ago: int = 0,
    chunk_text: str | None = None,
) -> Document:
    document = Document(
        title=title,
        document_type="facility_agreement",
        counterparty="PQR Bank",
        document_date=date(2026, 1, 1),
        department=department,
        storage_path=f"{uuid.uuid4()}/original.pdf",
        ingestion_status=ingestion_status,
        review_status=review_status,
        ingestion_error=ingestion_error,
        uploaded_by_id=uploaded_by.id if uploaded_by else None,
        created_at=datetime.now(UTC) - timedelta(days=days_ago),
    )
    session.add(document)
    session.flush()
    if chunk_text is not None:
        session.add(
            DocumentChunk(document_id=document.id, chunk_index=0, page_number=1, text=chunk_text)
        )
    session.commit()
    return document


def _last_audit(session: Session) -> AuditLog:
    row = session.scalars(select(AuditLog).order_by(AuditLog.timestamp.desc())).first()
    assert row is not None
    return row


# ---------------------------------------------------------------- pure resolution


def test_resolve_states() -> None:
    now = datetime.now(UTC)
    proc = pending_documents.PendingDocument(uuid.uuid4(), "İşlenen", "ocr", now, "finans", None)
    bad = pending_documents.PendingDocument(
        uuid.uuid4(), "Bozuk", "failed", now, "finans", ingestion_errors.REASONS["corrupt"]
    )
    assert pending_documents.resolve(False, []) == pending_documents.NO_PENDING
    a = pending_documents.resolve(False, [proc, bad])
    assert a.state == "A" and a.notice == pending_documents.PROCESSING_NOTICE
    assert a.documents == (proc, bad)
    b = pending_documents.resolve(False, [bad])
    assert b.state == "B" and b.notice == pending_documents.UNREADABLE_NOTICE
    c = pending_documents.resolve(True, [proc, bad])
    assert c.state == "C" and c.documents == (proc,)
    assert c.notice == pending_documents.CHANGE_NOTICE_PREFIX + "İşlenen"
    assert pending_documents.resolve(True, [bad]) == pending_documents.NO_PENDING


# ---------------------------------------------------------------- flag off: byte-identical


def test_flag_off_carries_nothing_even_with_a_matching_processing_document(
    client: TestClient, db_session: Session, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    _pending(db_session, title="Facility Agreement Amendment 03", department=None)
    body = _ask(client, "Facility Agreement Amendment 03 ne diyor?")
    assert body["answered"] is False and body["answer"] == NO_ANSWER_TEXT
    assert body["pending_notice"] is None and body["pending_documents"] == []
    assert body["warnings"][0]["kind"] == "missing_data"
    assert _last_audit(db_session).assist is None


# ---------------------------------------------------------------- T7-3: state A


def test_question_naming_a_processing_document_gets_state_a_without_an_llm_call(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    doc = _pending(db_session, title="Facility Agreement Amendment 03", department=None)
    body = _ask(client, "Facility Agreement Amendment 03 ne diyor?")

    assert fake_llm.requests == []  # zero chunks: ADR-021 still holds
    assert body["answered"] is False and body["answer"] == NO_ANSWER_TEXT  # SORU 6 (i)
    assert body["pending_notice"] == pending_documents.PROCESSING_NOTICE
    assert [d["document_id"] for d in body["pending_documents"]] == [str(doc.id)]
    assert body["pending_documents"][0]["status"] == "ocr"
    assert body["pending_documents"][0]["reason"] is None
    assert [w["kind"] for w in body["warnings"]] == ["document_processing"]
    assert body["warnings"][0]["message"] == pending_documents.PROCESSED_NOTE
    assert body["warnings"][0]["action"] is None
    assert body["assist"] is not None  # SORU 7: the clarify block still rides along
    audit = _last_audit(db_session).assist
    assert audit["pending_state"] == "A" and audit["pending_notice"] == body["pending_notice"]
    assert [d["document_id"] for d in audit["pending_documents"]] == [str(doc.id)]


# ---------------------------------------------------------------- state B


def test_unreadable_matching_document_gets_state_b_with_the_turkish_reason(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    doc = _pending(
        db_session,
        title="Sigorta Poliçesi 2026",
        department=None,
        ingestion_status=IngestionStatus.failed,
        ingestion_error="encrypted",
    )
    body = _ask(client, "Sigorta poliçesi ne zaman bitiyor?")

    assert body["answered"] is False and body["answer"] == NO_ANSWER_TEXT
    assert body["pending_notice"] == pending_documents.UNREADABLE_NOTICE
    assert body["pending_documents"][0]["document_id"] == str(doc.id)
    assert body["pending_documents"][0]["status"] == "failed"
    assert body["pending_documents"][0]["reason"] == ingestion_errors.REASONS["encrypted"]
    assert "encrypted" not in json.dumps(body)  # the raw code never leaves
    assert [w["kind"] for w in body["warnings"]] == ["document_unreadable"]


# ---------------------------------------------------------------- T7-4: the gate (G3)


def test_other_departments_processing_document_is_never_mentioned(
    client: TestClient,
    db_session: Session,
    employee_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    enerji = make_department(db_session, slug="enerji")
    make_department(db_session, slug="finans")
    add_user_to_department(db_session, employee_user, enerji)
    _pending(db_session, title="Finans Kredi Sözleşmesi Ek 2", department="finans")
    _pending(
        db_session,
        title="Finans Teminat Mektubu",
        department="finans",
        ingestion_status=IngestionStatus.failed,
        ingestion_error="corrupt",
    )

    body = _ask(client, "Finans kredi sözleşmesi ek 2 teminat mektubu ne diyor?")

    assert body["answered"] is False
    assert body["pending_notice"] is None and body["pending_documents"] == []
    assert [w["kind"] for w in body["warnings"]] == ["missing_data"]  # state D
    assert "Finans Kredi" not in json.dumps(body, ensure_ascii=False)
    assert "Teminat" not in json.dumps(body, ensure_ascii=False)
    assert _last_audit(db_session).assist.get("pending_documents", []) == []


def test_own_pending_upload_is_listed_but_its_text_never_reaches_the_prompt(
    client: TestClient,
    db_session: Session,
    employee_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    """Naci SORU 9: the handling scope (`include_pending`) feeds the pending list only —
    retrieval keeps the approved-only gate. A not-yet-approved document with chunk text is
    *listed* as processing and *never* retrieved or shown to the model."""
    finans = make_department(db_session, slug="finans")
    add_user_to_department(db_session, employee_user, finans)
    _document(db_session, title="Facility", department="finans", text="DSCR covenant 1,25x")
    mine = _pending(
        db_session,
        title="DSCR Covenant Raporu Taslak",
        department="finans",
        review_status=DocumentReviewStatus.pending_metadata,
        uploaded_by=employee_user,
        chunk_text=f"DSCR covenant {SENTINEL}",
    )
    fake_llm.replies = ["DSCR covenant 1,25x'tir [K1]."]

    body = _ask(client, "DSCR covenant raporu nedir?", department="finans")

    assert SENTINEL not in fake_llm.prompt_text()
    assert str(mine.id) not in body["retrieved_document_ids"]
    assert body["answered"] is True
    assert body["pending_notice"] == pending_documents.CHANGE_NOTICE_PREFIX + mine.title  # state C
    assert [d["document_id"] for d in body["pending_documents"]] == [str(mine.id)]
    assert [w["kind"] for w in body["warnings"]] == []


# ---------------------------------------------------------------- T7-5: state C


def test_answered_question_with_a_processing_document_on_the_same_topic_gets_a_note(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    _document(db_session, title="Facility", department=None, text="DSCR covenant 1,25x")
    new = _pending(db_session, title="Facility Agreement Amendment 04", department=None)
    fake_llm.replies = ["DSCR covenant 1,25x'tir [K1]."]

    body = _ask(client, "Facility agreement DSCR covenant nedir?")

    assert body["answered"] is True and body["sources"]
    assert body["pending_notice"] == pending_documents.CHANGE_NOTICE_PREFIX + new.title
    assert body["pending_documents"][0]["document_id"] == str(new.id)
    assert body["warnings"] == [] and body["assist"] is None
    assert _last_audit(db_session).assist["pending_state"] == "C"


# ---------------------------------------------------------------- T7-6: unrelated → D


def test_unrelated_processing_document_is_not_mentioned(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    db_session.add_all(
        [Project(name="Ankara RES", code="ANK_RES"), Project(name="İzmir RES", code="IZM_RES")]
    )
    db_session.commit()
    _pending(db_session, title="Ankara RES Personel Listesi", department=None)
    _pending(db_session, title="İzmir RES ÇED Raporu", department=None)

    # "Ankara"/"RES" are project words: a project name alone never matches (plan §3).
    body = _ask(client, "Ankara RES kredi faiz oranı nedir?")

    assert body["pending_notice"] is None and body["pending_documents"] == []
    assert [w["kind"] for w in body["warnings"]] == ["missing_data"]


def test_old_processing_document_outside_the_window_is_ignored_but_failed_stays(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    _pending(db_session, title="Teminat Mektubu Eski", department=None, days_ago=30)
    old_failed = _pending(
        db_session,
        title="Teminat Mektubu Okunamayan",
        department=None,
        ingestion_status=IngestionStatus.failed,
        ingestion_error="no_text",
        days_ago=30,
    )
    body = _ask(client, "Teminat mektubu tutarı nedir?")
    assert [d["document_id"] for d in body["pending_documents"]] == [str(old_failed.id)]
    assert body["pending_notice"] == pending_documents.UNREADABLE_NOTICE


def test_at_most_three_documents_newest_first(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    docs = [
        _pending(db_session, title=f"Teminat Mektubu {i}", department=None, days_ago=4 - i)
        for i in range(5)
    ]
    body = _ask(client, "Teminat mektubu tutarı nedir?")
    assert [d["title"] for d in body["pending_documents"]] == [
        docs[4].title,
        docs[3].title,
        docs[2].title,
    ]


def test_mixed_no_answer_keeps_the_fixed_sentence_inside_and_adds_the_notice(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_router: FakeRouter,
    assist_on: None,
) -> None:
    """MIXED: the document half ran → the pending check runs; the fixed sentence stays
    inside the merged answer (eval G2's MIXED rule) and the notice rides alongside."""
    fake_router.query_type = "MIXED_QUERY"
    _pending(db_session, title="Kredi Ödeme Planı", department=None)
    body = _ask(client, "Kredi ödeme planı nedir?")
    assert body["query_type"] == "MIXED_QUERY"
    assert DOCUMENT_PART_HEADING in body["answer"] and NO_ANSWER_TEXT in body["answer"]
    assert body["pending_notice"] == pending_documents.PROCESSING_NOTICE
    assert [w["kind"] for w in body["warnings"]] == ["document_processing"]
