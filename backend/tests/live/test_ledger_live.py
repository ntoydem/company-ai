"""Ledger acceptance criteria 1-3 against the real LLM (`make test-llm`).

Skipped unless LLM_LIVE_TESTS=1 and LLM_API_KEY are set. Replaces the Adım 0
`test_t0_live.py` (Phase 3.1: T0 removed) — same 3 criteria, ledger-generated documents
and ledger values instead of the old temporary T0 figures (SORU 4, PHASE_3_1_PLAN.md).
"""

from __future__ import annotations

import os
import re
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.user import User
from app.services.answer_prompt import NO_ANSWER_TEXT
from tests.ledger_fixtures import ledger_value, load_ledger_documents

pytestmark = pytest.mark.live_llm

_TURKISH_CHARS = re.compile(r"[çğıöşüÇĞİÖŞÜ]")
_ENGLISH_WORDS = re.compile(r"\b(the|is|are|was|were|shall)\b")

_FACILITY_REF, _AMENDMENT_REF = "DOC-ANK-FIN-004", "DOC-ANK-FIN-005"


@pytest.fixture(autouse=True)
def _require_live(settings: Settings) -> None:
    if os.environ.get("LLM_LIVE_TESTS") != "1":
        pytest.skip("LLM_LIVE_TESTS=1 not set")
    if not (settings.llm_api_key and settings.llm_api_key.get_secret_value()):
        pytest.skip("LLM_API_KEY not set")


# Gemini free tier: 5 requests / minute on the answer model. Space calls out and, on a
# 503 (rate limit mapped by the API), wait for the window to reset and try once more.
_CALL_SPACING_S = 13
_RATE_LIMIT_WAIT_S = 65


def _ask(client: TestClient, question: str) -> dict[str, object]:
    time.sleep(_CALL_SPACING_S)
    response = client.post("/api/ask", json={"question": question})
    if response.status_code == 503:
        time.sleep(_RATE_LIMIT_WAIT_S)
        response = client.post("/api/ask", json={"question": question})
    assert response.status_code == 200, response.text
    body: dict[str, object] = response.json()
    print(f"\nSORU: {question}\nCEVAP: {body['answer']}\nKAYNAKLAR: {body['sources']}")
    return body


def _assert_turkish(answer: str) -> None:
    assert _TURKISH_CHARS.search(answer), answer
    assert not _ENGLISH_WORDS.search(answer.lower()), answer


def _ratio_aliases(value: float) -> tuple[str, str]:
    comma = f"{value:.2f}".rstrip("0").rstrip(".").replace(".", ",")
    dot = f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{comma}x", f"{dot}x"


def _value_in(answer: str, *aliases: str) -> bool:
    return any(alias in answer for alias in aliases)


def test_current_dscr_is_amendment(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    """Kabul kriteri 1 (questions.json ANK-FIN-006)."""
    load_ledger_documents(db_session, [_FACILITY_REF, _AMENDMENT_REF])
    current = ledger_value("ankara_res.project.finance.dscr_covenant.current.value")
    body = _ask(client, "Ankara RES'in güncel minimum DSCR covenant'ı nedir?")
    answer = str(body["answer"])
    sources = body["sources"]
    assert body["answered"] is True
    assert _value_in(answer, *_ratio_aliases(current))
    assert isinstance(sources, list) and sources
    assert (
        sources[0]["title"] == "Facility Agreement Amendment 01"
        and sources[0]["is_current"] is True
    )
    _assert_turkish(answer)


def test_initial_dscr_is_executed_and_differs(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    """Kabul kriteri 2 (questions.json ANK-FIN-007)."""
    load_ledger_documents(db_session, [_FACILITY_REF, _AMENDMENT_REF])
    initial = ledger_value("ankara_res.project.finance.dscr_covenant.initial.value")
    current_answer = str(
        _ask(client, "Ankara RES'in güncel minimum DSCR covenant'ı nedir?")["answer"]
    )
    body = _ask(client, "İlk DSCR covenant neydi?")
    answer = str(body["answer"])
    sources = body["sources"]
    assert body["answered"] is True
    assert _value_in(answer, *_ratio_aliases(initial))
    assert isinstance(sources, list)
    facility = [s for s in sources if s["title"] == "Facility Agreement"]
    assert facility and facility[0]["status"] == "superseded"
    # The first sentence (the answer proper) carries the historical value, not the current one.
    first_sentence = re.split(r"(?<=[.!?])\s", answer, maxsplit=1)[0]
    assert _value_in(first_sentence, *_ratio_aliases(initial))
    assert answer != current_answer
    _assert_turkish(answer)


def test_izmir_cod_no_answer(client: TestClient, db_session: Session, admin_user: User) -> None:
    """Kabul kriteri 3 (questions.json GEN-HAL-001) — retrieval *does* return Ankara
    chunks here (OR semantics on "RES"); the refusal comes from the model honouring
    rules 2 and 3."""
    load_ledger_documents(db_session, [_FACILITY_REF, _AMENDMENT_REF])
    body = _ask(client, "İzmir RES'in COD tarihi nedir?")
    assert body["retrieved_document_ids"], "Ankara chunks were offered to the model"
    assert body["answered"] is False
    assert body["answer"] == NO_ANSWER_TEXT
    assert body["sources"] == []
