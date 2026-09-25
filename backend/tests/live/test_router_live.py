"""Phase 4.3 acceptance criteria against the real router + real LLM (`make test-llm`):
routing of the SPEC_04 §7 examples, the ambiguous-DSCR MIXED answer, the Q3 2024 variance
MIXED answer (SORU 1 rewording), and the GENERAL branch. Skipped unless LLM_LIVE_TESTS=1.

Pacing: Gemini free tier is 5 requests/min per model; `.env` uses the same model for
classify and answer, so every call sleeps 13 s × the LLM requests it will make."""

from __future__ import annotations

import os
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.user import User
from app.schemas.ask import GENERAL_NOTICE
from app.services.answer_prompt import NO_ANSWER_TEXT, NO_REASON_TEXT
from app.services.ask_router import DATA_PART_HEADING, DOCUMENT_PART_HEADING
from app.services.llm import build_llm_client
from app.services.router import LLMRouter
from tests.ledger_fixtures import ledger_value, load_ledger_documents
from tests.test_excel_api import _upload_workbook

pytestmark = pytest.mark.live_llm

_PER_REQUEST_S = 13
_RATE_LIMIT_WAIT_S = 65


@pytest.fixture(autouse=True)
def _require_live(settings: Settings) -> None:
    if os.environ.get("LLM_LIVE_TESTS") != "1":
        pytest.skip("LLM_LIVE_TESTS=1 not set")
    if not (settings.llm_api_key and settings.llm_api_key.get_secret_value()):
        pytest.skip("LLM_API_KEY not set")


def _ask(client: TestClient, question: str, *, llm_requests: int) -> dict[str, object]:
    time.sleep(_PER_REQUEST_S * llm_requests)
    response = client.post("/api/ask", json={"question": question})
    if response.status_code == 503:
        time.sleep(_RATE_LIMIT_WAIT_S)
        response = client.post("/api/ask", json={"question": question})
    assert response.status_code == 200, response.text
    body: dict[str, object] = response.json()
    print(
        f"\nSORU: {question}\nTİP: {body['query_type']}\nCEVAP: {body['answer']}\n"
        f"KAYNAKLAR: {body['sources']}\nEXCEL: {body['excel_sources']}\n"
        f"TOKEN: {body['tokens_in']}/{body['tokens_out']}"
    )
    return body


def _ratio_aliases(value: float) -> tuple[str, ...]:
    exact = f"{value:.2f}"
    return (f"{exact.replace('.', ',')}x", f"{exact}x")


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("Kredi sözleşmesindeki DSCR covenant nedir?", "DOCUMENT_QUERY"),
        ("Ankara RES 2026 Q2 DSCR kaç?", "DATA_QUERY"),
        ("Güncel DSCR kaç?", "MIXED_QUERY"),
        ("DSCR ne demek?", "GENERAL_QUERY"),
        ("İzmir RES'in COD tarihi nedir?", "DOCUMENT_QUERY"),
    ],
)
def test_router_classifies_spec_examples(settings: Settings, question: str, expected: str) -> None:
    """SPEC_04 §7 examples through the real classifier only (one request each) — the
    measurement behind PHASES.md's "Gemini yeterli mi?" decision point."""
    time.sleep(_PER_REQUEST_S)
    routed = LLMRouter(build_llm_client(settings), settings).route(question)
    print(
        f"\nROUTE: {question} -> {routed.query_type} ({routed.reason}) "
        f"doc={routed.document_question!r} data={routed.data_question!r}"
    )
    assert routed.query_type == expected


def test_ambiguous_dscr_returns_covenant_and_realised_values(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    """PHASES.md 4.3: belirsiz DSCR → iki değer iki kaynak türü."""
    load_ledger_documents(db_session, ["DOC-ANK-FIN-004", "DOC-ANK-FIN-005"])
    _upload_workbook(client)  # Covenant_Report.xlsx
    covenant = ledger_value("ankara_res.project.finance.dscr_covenant.current.value")
    realised = ledger_value("ankara_res.project.finance.covenant_tests[10].dscr")

    body = _ask(client, "Güncel DSCR kaç?", llm_requests=4)

    assert body["query_type"] == "MIXED_QUERY" and body["answered"] is True
    answer = str(body["answer"])
    document_part, data_part = answer.split(f"\n\n{DATA_PART_HEADING}\n")
    assert document_part.startswith(DOCUMENT_PART_HEADING)
    assert any(a in document_part for a in _ratio_aliases(covenant)), document_part
    assert any(a in data_part for a in _ratio_aliases(realised)), data_part
    sources = body["sources"]
    assert isinstance(sources, list) and sources
    assert sources[0]["title"] == "Facility Agreement Amendment 01"
    excel_sources = body["excel_sources"]
    assert isinstance(excel_sources, list) and excel_sources
    assert excel_sources[0]["label"] == "Covenant_Report.xlsx Q2_2026!D14"


def test_budget_variance_with_no_reason_in_documents(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    """PHASES.md 4.3 (SORU 1): Excel farkı + yalnızca belgedeki sebep — none is stated, so
    the document side is the rule-6 sentence or the no-answer text, never an invented one."""
    load_ledger_documents(db_session, ["DOC-ANK-OPS-001", "DOC-ANK-FIN-007"])
    _upload_workbook(client, "Budget_vs_Actual_2026.xlsx")

    body = _ask(
        client,
        "Ankara RES Q3 2024 bütçe sapması neydi ve sebebi belgelerde yazıyor mu?",
        llm_requests=4,
    )

    assert body["query_type"] == "MIXED_QUERY" and body["answered"] is True
    answer = str(body["answer"])
    document_part, data_part = answer.split(f"\n\n{DATA_PART_HEADING}\n")
    assert "-894.000 TRY" in data_part, data_part
    excel_sources = body["excel_sources"]
    assert isinstance(excel_sources, list)
    assert excel_sources[0]["label"] == "Budget_vs_Actual_2026.xlsx Summary!D5"
    assert NO_REASON_TEXT in document_part or NO_ANSWER_TEXT in document_part, document_part
    for invented in ("arıza", "dişli", "kesinti", "rüzgar"):
        assert invented not in document_part.lower(), document_part


def test_general_question_states_no_company_data(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    """PHASES.md 4.3: GENERAL sorularda şirket verisi kullanılmaz ve bu belirtilir."""
    load_ledger_documents(db_session, ["DOC-ANK-FIN-004", "DOC-ANK-FIN-005"])
    _upload_workbook(client)

    body = _ask(client, "DSCR ne demek?", llm_requests=2)

    assert body["query_type"] == "GENERAL_QUERY"
    assert str(body["answer"]).startswith(GENERAL_NOTICE)
    assert body["sources"] == [] and body["excel_sources"] == []
    assert body["retrieved_document_ids"] == []
    assert "Ankara" not in str(body["answer"])
