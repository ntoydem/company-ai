"""`POST /api/ask` with a fake LLM — T0 criterion 4 (only allowed chunks reach the prompt),
the no-source path, citation parsing and error mapping. No network."""

from __future__ import annotations

import logging
import re
import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_llm_client
from app.core.errors import LLM_NOT_CONFIGURED_MESSAGE, LLM_UNAVAILABLE_MESSAGE
from app.main import app
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.repositories import audit_log_repo
from app.schemas.ask import NO_INTERPRETATION_NOTICE
from app.services import retrieval as retrieval_module
from app.services.answer_prompt import NO_ANSWER_TEXT
from app.services.llm import LLMNotConfiguredError, LLMRateLimitError, LLMRequest
from tests.department_fixtures import add_user_to_department, make_department
from tests.fakes import FakeLLMClient
from tests.ledger_fixtures import ensure_generated_documents, load_ledger_documents

SENTINEL = "SENTINEL-GIZLI-HUKUK-METNI"


def _document(
    session: Session, *, title: str, department: str | None, text: str, page: int = 1
) -> Document:
    document = Document(
        title=title,
        document_type="facility_agreement",
        counterparty="PQR Bank",
        document_date=date(2023, 6, 1),
        department=department,
        status=DocumentStatus.executed,
        storage_path=f"{uuid.uuid4()}/original.pdf",
    )
    session.add(document)
    session.flush()
    session.add(DocumentChunk(document_id=document.id, chunk_index=0, page_number=page, text=text))
    session.commit()
    return document


def _ask(client: TestClient, question: str, **extra: object) -> dict[str, object]:
    response = client.post("/api/ask", json={"question": question, **extra})
    assert response.status_code == 200, response.text
    body: dict[str, object] = response.json()
    return body


def test_prompt_contains_only_allowed_chunks(
    client: TestClient, db_session: Session, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    """Kabul kriteri 4: the legal document is outside the `finance` scope, so its text must
    never appear in the prompt — enforced by the real SQL provider behind
    `allowed_document_ids`, not by a fake."""
    a = _document(db_session, title="Facility", department="finance", text="DSCR covenant 1,25x A")
    b = _document(db_session, title="Amendment", department="finance", text="DSCR covenant 1,20x B")
    c = _document(
        db_session, title="Legal memo", department="legal", text=f"DSCR covenant {SENTINEL}"
    )

    body = _ask(client, "DSCR covenant nedir?", department="finance")

    prompt = fake_llm.prompt_text()
    assert "DSCR covenant 1,25x A" in prompt and "DSCR covenant 1,20x B" in prompt
    assert SENTINEL not in prompt
    assert set(body["retrieved_document_ids"]) == {str(a.id), str(b.id)}  # type: ignore[arg-type]
    assert str(c.id) not in body["retrieved_document_ids"]  # type: ignore[operator]

    # Control: without the scope the same document *is* retrieved — the exclusion above
    # came from the authorization gate, not from retrieval missing the text.
    _ask(client, "DSCR covenant nedir?")
    assert SENTINEL in fake_llm.prompt_text(1)


def test_prompt_respects_gate_subset(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Whatever `allowed_document_ids` returns is the upper bound of what the prompt sees."""
    a = _document(db_session, title="A", department=None, text="DSCR covenant metin A")
    _document(db_session, title="B", department=None, text=f"DSCR covenant {SENTINEL}")
    monkeypatch.setattr(retrieval_module, "allowed_document_ids", lambda *_: {a.id})

    body = _ask(client, "DSCR covenant nedir?")
    assert "DSCR covenant metin A" in fake_llm.prompt_text()
    assert SENTINEL not in fake_llm.prompt_text()
    assert body["retrieved_document_ids"] == [str(a.id)]


def test_empty_gate_means_no_llm_call(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _document(db_session, title="A", department=None, text="DSCR covenant 1,25x")
    monkeypatch.setattr(retrieval_module, "allowed_document_ids", lambda *_: set())

    body = _ask(client, "DSCR covenant nedir?")
    assert fake_llm.requests == []
    assert body["answered"] is False and body["answer"] == NO_ANSWER_TEXT
    assert body["sources"] == [] and body["retrieved_document_ids"] == []


def test_no_chunks_means_no_llm_call_and_zero_tokens(
    client: TestClient, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    body = _ask(client, "İzmir RES'in COD tarihi nedir?")
    assert fake_llm.requests == []
    assert body["answered"] is False and body["answer"] == NO_ANSWER_TEXT
    assert (body["tokens_in"], body["tokens_out"], body["model"]) == (0, 0, None)
    assert body["notice"] == NO_INTERPRETATION_NOTICE


def test_sources_come_from_citations_with_page_and_chain(
    client: TestClient, db_session: Session, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    """Kabul kriteri (Phase 3.1 taşıması): sayfa numaraları ve tarihler ledger'ın
    `manifest.json`'ından okunur, testte hiçbir rakam sabit yazılmaz (plan T9)."""
    manifest = ensure_generated_documents()
    by_ref = {e["external_ref"]: e for e in manifest["documents"]}
    facility_entry, amendment_entry = by_ref["DOC-ANK-FIN-004"], by_ref["DOC-ANK-FIN-005"]
    documents = load_ledger_documents(db_session, ["DOC-ANK-FIN-004", "DOC-ANK-FIN-005"])
    facility, amendment = documents["DOC-ANK-FIN-004"], documents["DOC-ANK-FIN-005"]

    facility_page = facility_entry["page_map"]["5. Financial Covenants"]
    amendment_page = amendment_entry["page_map"]["2. Amendments to the Original Agreement"]

    def reply(request: LLMRequest) -> str:
        """Cite the amendment's own covenant-change section and the executed facility's
        financial-covenants section, whatever labels the prompt gave them — plus a label
        that does not exist."""
        match_amendment = re.search(
            rf"\[(K\d+)\] Belge: {re.escape(amendment.title)} \|.*?Sayfa: {amendment_page}\n",
            request.user,
        )
        match_facility = re.search(
            rf"\[(K\d+)\] Belge: {re.escape(facility.title)} \|.*?Sayfa: {facility_page}\n",
            request.user,
        )
        assert match_amendment and match_facility, request.user
        return (
            f"Ankara RES'in güncel minimum DSCR covenant'ı [{match_amendment.group(1)}]'de "
            f"belirtilmiştir. İlk covenant seviyesi [{match_facility.group(1)}]'de yer "
            "almaktadır. Uydurma [K99]."
        )

    fake_llm.reply_fn = reply
    body = _ask(client, "Ankara RES'in güncel minimum DSCR covenant'ı nedir?")

    assert body["answered"] is True
    sources = body["sources"]
    assert isinstance(sources, list) and len(sources) == 2
    first, second = sources
    assert first["title"] == amendment.title and first["page_number"] == amendment_page
    assert first["is_current"] is True and first["supersedes_title"] == facility.title
    assert first["document_date"] == amendment.document_date.isoformat()
    assert first["version"] == amendment_entry["version_number"]
    assert second["title"] == facility.title and second["page_number"] == facility_page
    assert second["is_current"] is False and second["superseded_by_title"] == amendment.title
    assert second["status"] == "superseded"
    # The prompt carried the chain flags computed in code, current document first.
    prompt = fake_llm.requests[0].user
    assert prompt.index("Zincir: GÜNCEL") < prompt.index("Zincir: İLK HALKA")
    assert "BUGÜN: 15.09.2026" in prompt
    assert str(facility.id) in body["retrieved_document_ids"]  # type: ignore[operator]
    assert str(amendment.id) in body["retrieved_document_ids"]  # type: ignore[operator]


def test_no_answer_reply_is_canonicalized(
    client: TestClient, db_session: Session, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    _document(db_session, title="A", department=None, text="Ankara RES DSCR covenant 1,25x")
    fake_llm.replies = ["Üzgünüm, mevcut şirket kaynaklarında yeterli bilgi bulamadım."]

    body = _ask(client, "İzmir RES DSCR covenant nedir?")
    assert fake_llm.requests, "chunks were retrieved, so the model was consulted"
    assert body["answered"] is False and body["answer"] == NO_ANSWER_TEXT
    assert body["sources"] == []
    assert body["tokens_in"] == 123


def test_llm_failure_returns_503_without_detail(
    client: TestClient, db_session: Session, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    _document(db_session, title="A", department=None, text="DSCR covenant 1,25x")
    fake_llm.error = LLMRateLimitError("quota exceeded for key sk-secret")

    response = client.post("/api/ask", json={"question": "DSCR covenant nedir?"})
    assert response.status_code == 503
    assert response.json()["detail"] == LLM_UNAVAILABLE_MESSAGE
    assert "sk-secret" not in response.text


def test_not_configured_returns_503(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    _document(db_session, title="A", department=None, text="DSCR covenant 1,25x")

    def raise_not_configured() -> FakeLLMClient:
        raise LLMNotConfiguredError("LLM_API_KEY is not set")

    app.dependency_overrides[get_llm_client] = raise_not_configured
    try:
        response = client.post("/api/ask", json={"question": "DSCR covenant nedir?"})
    finally:
        app.dependency_overrides.pop(get_llm_client, None)
    assert response.status_code == 503
    assert response.json()["detail"] == LLM_NOT_CONFIGURED_MESSAGE


def test_question_validation(client: TestClient, admin_user: User, fake_llm: FakeLLMClient) -> None:
    assert client.post("/api/ask", json={"question": "ab"}).status_code == 422
    assert client.post("/api/ask", json={}).status_code == 422


def test_ask_completed_log_carries_token_counts(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Kabul kriteri 5: token counts are logged (here from the service; the client-level
    `llm call` record is covered in test_llm_client.py)."""
    _document(db_session, title="A", department=None, text="DSCR covenant 1,25x")
    with caplog.at_level(logging.INFO, logger="app.services.ask"):
        _ask(client, "DSCR covenant nedir?")
    record = next(r for r in caplog.records if r.getMessage() == "ask completed")
    assert record.tokens_in == 123 and record.tokens_out == 45  # type: ignore[attr-defined]
    assert record.model == "fake-model"  # type: ignore[attr-defined]
    assert record.answered is True  # type: ignore[attr-defined]


def test_employee_ask_outside_department_returns_no_answer_with_empty_retrieved(
    client: TestClient,
    db_session: Session,
    employee_user: User,
    fake_llm: FakeLLMClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Kabul kriteri 1: enerji → finans belgesiyle ilgili soruya `/api/ask` ile "bilgi
    bulamadım"; `retrieved_document_ids` boş — bu, `audit_log` tablosu gelene kadar (Phase
    3.4) audit kanıtı olarak kullanılır (docs/plans/PHASE_1_2_PLAN.md T5)."""
    enerji = make_department(db_session, slug="enerji_grubu")
    add_user_to_department(db_session, employee_user, enerji)
    _document(db_session, title="A", department="finans", text=f"DSCR covenant {SENTINEL}")

    with caplog.at_level(logging.INFO, logger="app.services.ask"):
        body = _ask(client, "DSCR covenant nedir?")

    assert body["answered"] is False
    assert body["answer"] == NO_ANSWER_TEXT
    assert body["retrieved_document_ids"] == []
    record = next(r for r in caplog.records if r.getMessage() == "ask completed")
    assert record.retrieved_document_ids == []  # type: ignore[attr-defined]


# --- Phase 3.4: every /api/ask call is audited (SPEC_06 §1) ---


def _only_row(session: Session):  # noqa: ANN202 — test helper, mypy doesn't check tests/
    rows = audit_log_repo.list_filtered(session, limit=10)
    assert len(rows) == 1, rows
    return rows[0]


def test_audit_log_written_for_an_answered_question(
    client: TestClient, db_session: Session, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    document = _document(db_session, title="A", department="finans", text="DSCR covenant 1,25x")

    response = client.post(
        "/api/ask",
        json={"question": "DSCR covenant nedir?", "department": "finans"},
        headers={"X-Request-ID": "test-req-id"},
    )
    assert response.status_code == 200

    row = _only_row(db_session)
    assert row.user_id == admin_user.id
    assert row.question == "DSCR covenant nedir?"
    assert row.query_type == "DOCUMENT_QUERY"
    assert row.scope_department == "finans"
    assert row.documents_retrieved == [document.id]
    assert row.answer == response.json()["answer"]
    assert row.sources and row.sources[0]["title"] == "A"
    assert row.model == "fake-model"
    assert (row.tokens_in, row.tokens_out) == (123, 45)
    assert row.cost_estimate is None
    assert row.execution_ms >= 0
    assert row.request_id == "test-req-id"
    assert row.error is None


def test_audit_log_written_when_no_chunks_retrieved(
    client: TestClient, admin_user: User, fake_llm: FakeLLMClient, db_session: Session
) -> None:
    response = client.post("/api/ask", json={"question": "İzmir RES'in COD tarihi nedir?"})
    assert response.status_code == 200

    row = _only_row(db_session)
    assert row.answer == NO_ANSWER_TEXT
    assert row.documents_retrieved == []
    assert row.model is None
    assert row.error is None
    assert fake_llm.requests == []  # confirms this really is the zero-chunk path


def test_audit_log_written_with_error_on_llm_failure_and_response_unaffected(
    client: TestClient, db_session: Session, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    _document(db_session, title="A", department=None, text="DSCR covenant 1,25x")
    fake_llm.error = LLMRateLimitError("quota exceeded for key sk-secret")

    response = client.post("/api/ask", json={"question": "DSCR covenant nedir?"})

    assert response.status_code == 503
    assert response.json()["detail"] == LLM_UNAVAILABLE_MESSAGE
    row = _only_row(db_session)
    assert row.error is not None and "quota exceeded" in row.error
    assert row.answer == ""
    assert row.model is None
    assert (row.tokens_in, row.tokens_out) == (0, 0)


def test_audit_log_write_failure_never_breaks_the_response(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ADR-006 pattern: a broken audit write must not break the answer the user already
    has — `/api/ask` still returns 200, no exception propagates."""
    from app.services import ask as ask_module

    _document(db_session, title="A", department=None, text="DSCR covenant 1,25x")

    def _boom(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("db is on fire")

    monkeypatch.setattr(ask_module.audit_log_repo, "create", _boom)

    response = client.post("/api/ask", json={"question": "DSCR covenant nedir?"})

    assert response.status_code == 200
    assert response.json()["answered"] is True
