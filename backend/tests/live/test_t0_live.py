"""T0 acceptance criteria 1–3 and 5a against the real LLM (`make test-llm`).

Skipped unless LLM_LIVE_TESTS=1 and LLM_API_KEY are set. Uses the real T0 PDFs (page text
via PyMuPDF) with the Facility Agreement → Amendment 01 chain; the answers are Gemini's.
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
from tests.t0_fixtures import load_t0_documents

pytestmark = pytest.mark.live_llm

_TURKISH_CHARS = re.compile(r"[çğıöşüÇĞİÖŞÜ]")
_ENGLISH_WORDS = re.compile(r"\b(the|is|are|was|were|shall)\b")


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


def _value_in(answer: str, *aliases: str) -> bool:
    return any(alias in answer for alias in aliases)


def test_current_dscr_is_amendment(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    """Kabul kriteri 1."""
    load_t0_documents(db_session)
    body = _ask(client, "Ankara RES'in güncel minimum DSCR covenant'ı nedir?")
    answer = str(body["answer"])
    sources = body["sources"]
    assert body["answered"] is True
    assert _value_in(answer, "1,20", "1.20", "1,2x", "1.2x")
    assert isinstance(sources, list) and sources
    assert sources[0]["title"] == "Amendment 01" and sources[0]["is_current"] is True
    assert sources[0]["page_number"] == 3
    _assert_turkish(answer)


def test_initial_dscr_is_executed_and_differs(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    """Kabul kriteri 2."""
    load_t0_documents(db_session)
    current = str(_ask(client, "Ankara RES'in güncel minimum DSCR covenant'ı nedir?")["answer"])
    body = _ask(client, "İlk DSCR covenant neydi?")
    answer = str(body["answer"])
    sources = body["sources"]
    assert body["answered"] is True
    assert _value_in(answer, "1,25", "1.25")
    assert isinstance(sources, list)
    facility = [s for s in sources if s["title"] == "Facility Agreement"]
    assert facility and facility[0]["status"] == "executed" and facility[0]["page_number"] == 6
    # The first sentence (the answer proper) carries the historical value, not the current one.
    first_sentence = re.split(r"(?<=[.!?])\s", answer, maxsplit=1)[0]
    assert _value_in(first_sentence, "1,25", "1.25") and not _value_in(first_sentence, "1,20")
    assert answer != current
    _assert_turkish(answer)


def test_izmir_cod_no_answer(client: TestClient, db_session: Session, admin_user: User) -> None:
    """Kabul kriteri 3 — retrieval *does* return Ankara chunks here (OR semantics on
    "RES"); the refusal comes from the model honouring rules 2 and 3."""
    load_t0_documents(db_session)
    body = _ask(client, "İzmir RES'in COD tarihi nedir?")
    assert body["retrieved_document_ids"], "Ankara chunks were offered to the model"
    assert body["answered"] is False
    assert body["answer"] == NO_ANSWER_TEXT
    assert body["sources"] == []
