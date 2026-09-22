"""`POST /api/ask` with a fake LLM — T0 criterion 4 (only allowed chunks reach the prompt),
the no-source path, citation parsing and error mapping. No network."""

from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Iterator
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
from app.schemas.ask import NO_INTERPRETATION_NOTICE
from app.services import retrieval as retrieval_module
from app.services.answer_prompt import NO_ANSWER_TEXT
from app.services.llm import LLMNotConfiguredError, LLMRateLimitError, LLMRequest
from tests.fakes import FakeLLMClient
from tests.t0_fixtures import load_t0_documents

SENTINEL = "SENTINEL-GIZLI-HUKUK-METNI"


@pytest.fixture
def fake_llm() -> Iterator[FakeLLMClient]:
    fake = FakeLLMClient()
    app.dependency_overrides[get_llm_client] = lambda: fake
    try:
        yield fake
    finally:
        app.dependency_overrides.pop(get_llm_client, None)


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
    facility, amendment = load_t0_documents(db_session)

    def reply(request: LLMRequest) -> str:
        """Cite the current document's first label and the Facility Agreement clause page,
        whatever labels the prompt gave them — plus a label that does not exist."""
        match = re.search(r"\[(K\d+)\] Belge: Facility Agreement \| .*?Sayfa: 6", request.user)
        assert match, request.user
        return (
            "Ankara RES'in güncel minimum DSCR covenant'ı 1,20x'tir [K1]. Bu değer Amendment 01 "
            f"ile önceki 1,25x seviyesinden değiştirilmiştir [{match.group(1)}]. Uydurma [K99]."
        )

    fake_llm.reply_fn = reply
    body = _ask(client, "Ankara RES'in güncel minimum DSCR covenant'ı nedir?")

    assert body["answered"] is True
    sources = body["sources"]
    assert isinstance(sources, list) and len(sources) == 2
    first, second = sources
    assert first["ref"] == "K1"
    assert first["title"] == "Amendment 01" and first["page_number"] == 3
    assert first["is_current"] is True and first["supersedes_title"] == "Facility Agreement"
    assert first["document_date"] == "2025-03-15" and first["version"] == 1
    assert second["title"] == "Facility Agreement" and second["page_number"] == 6
    assert second["is_current"] is False and second["superseded_by_title"] == "Amendment 01"
    assert second["status"] == "executed"
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
