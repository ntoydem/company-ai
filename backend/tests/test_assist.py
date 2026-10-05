"""ADR-027 (Tansu Not 2) — the assist block behind ASSIST_MODE: off = today's behaviour,
byte-identical; on = code-generated help next to the fixed no-answer sentence, no LLM on
the zero-chunk path, every suggestion inside the user's allowed set, the model's one
`SORU:` line kept only after code validation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.audit_log import AuditLog
from app.models.user import User
from app.services import ask as ask_module
from app.services import retrieval as retrieval_module
from app.services.answer_prompt import NO_ANSWER_TEXT, SYSTEM_PROMPT, SYSTEM_PROMPT_ASSIST
from app.services.assist import (
    CLARIFY_TEMPLATE,
    mismatch_terms,
    split_question_line,
    term_mismatch_template,
    validate_question,
)
from app.services.search_query import question_terms
from tests.fakes import FakeLLMClient
from tests.test_ask import _ask, _document

SORU = "Hangi dönemin sigorta poliçesini soruyorsunuz?"


@pytest.fixture
def assist_on(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "assist_mode_enabled", True)


# ---------------------------------------------------------------- pure helpers


def test_question_terms_drop_stopwords_and_suffixes() -> None:
    # "ne"/"nedir" are stopwords; "kadar" is not (it stays a search term, by design).
    assert question_terms("Ankara RES'in sigorta primi nedir?") == [
        "Ankara",
        "RES",
        "sigorta",
        "primi",
    ]
    assert question_terms("prim ne kadar?") == ["prim", "kadar"]
    assert question_terms("ne nedir mi?") == []


def test_mismatch_terms_ignore_generic_glossary_known_and_short_words() -> None:
    """A mismatch is a real word the corpus *and* the glossary lack: generic question words
    ("zaman", "değeri"), glossary-known words ("vadesi" → tenor, "ihracat kredi kurumu" →
    export credit agency) and three-letter tokens are not."""
    terms = [
        "Ankara",
        "RES",
        "kredisinin",
        "vadesi",
        "zaman",
        "ihracat",
        "kredi",
        "kurumu",
        "primi",
    ]
    assert mismatch_terms(terms, terms) == ["Ankara", "primi"]
    assert mismatch_terms(["DSKO", "RES", "değeri"], ["DSKO", "RES", "değeri"]) == ["DSKO"]


def test_split_question_line_separates_the_marker_line_only() -> None:
    text = f"{NO_ANSWER_TEXT}\nSORU: {SORU}"
    assert split_question_line(text) == (NO_ANSWER_TEXT, SORU)
    assert split_question_line("Vade 10 yıl [K1].") == ("Vade 10 yıl [K1].", None)
    assert split_question_line(f"soru: {SORU}\nkalan") == ("kalan", SORU)


def test_validate_question_refuses_facts_and_hidden_titles() -> None:
    ok, reason = validate_question(SORU, hidden_titles=["Gizli Hukuk Notu"])
    assert ok == SORU and reason is None
    cases = {
        "2025 poliçesini mi soruyorsunuz?": "contains a number, date, currency or percent",
        "Prim %5 mi?": "contains a number, date, currency or percent",
        "Hangi poliçe": "not a question",
        "Hangi poliçe? Yoksa sözleşme mi?": "more than one sentence",
        "Gizli Hukuk Notu belgesini mi soruyorsunuz?": "names a document outside the allowed set",
        "x" * 201 + "?": "too long",
        "   ": "empty",
    }
    for text, expected in cases.items():
        kept, why = validate_question(text, hidden_titles=["Gizli Hukuk Notu"])
        assert kept is None and why == expected, text


# ---------------------------------------------------------------- flag off: byte-identical


def test_flag_off_keeps_todays_contract(
    client: TestClient, db_session: Session, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    body = _ask(client, "Sigorta primi nedir?")
    assert fake_llm.requests == []
    assert body["answered"] is False and body["answer"] == NO_ANSWER_TEXT
    assert body["assist"] is None
    _document(db_session, title="Facility", department=None, text="DSCR covenant 1,25x")
    _ask(client, "DSCR covenant nedir?")
    assert fake_llm.requests[0].system == SYSTEM_PROMPT


# ---------------------------------------------------------------- zero chunks, flag on


def test_zero_chunks_clarify_without_any_llm_call(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    _document(db_session, title="Facility", department=None, text="DSCR covenant 1,25x")
    # "kapasite" is glossary-known (→ capacity) and "zaman" is a generic word: neither is a
    # terminology mismatch, so the help is a clarifying question, not a "term not found".
    body = _ask(client, "Kapasite ne zaman değişti?")
    assert fake_llm.requests == []  # ADR-021 holds with the flag on
    assert body["answered"] is False and body["answer"] == NO_ANSWER_TEXT
    assist = body["assist"]
    assert assist["kind"] == "clarify" and assist["question"] == CLARIFY_TEMPLATE
    assert assist["available"] == [] and assist["unmatched_terms"] == []
    assert (body["tokens_in"], body["tokens_out"], body["model"]) == (0, 0, None)

    # An unknown word (not in the corpus, not in the glossary) is a term mismatch even with
    # nothing else to show.
    body = _ask(client, "Bursa RES DSKO kaç?")
    assert fake_llm.requests == []
    assert body["assist"]["kind"] == "term_mismatch"
    assert body["assist"]["unmatched_terms"] == ["Bursa", "DSKO"]
    assert body["assist"]["question"] == term_mismatch_template(["Bursa", "DSKO"])


def test_zero_chunks_term_mismatch_lists_metadata_matches_from_allowed_documents(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    doc = _document(
        db_session, title="Sigorta Yenileme Bildirimi", department=None, text="poliçe yenilenmiştir"
    )
    body = _ask(client, "Sigorta primi nedir?")
    assert fake_llm.requests == []
    assist = body["assist"]
    assert assist["kind"] == "term_mismatch"
    # "Sigorta" is in an allowed title → matched (metadata); only "primi" is unknown.
    assert assist["unmatched_terms"] == ["primi"]
    assert assist["question"] == term_mismatch_template(["primi"])
    assert [a["document_id"] for a in assist["available"]] == [str(doc.id)]
    assert assist["available"][0]["title"] == "Sigorta Yenileme Bildirimi"


def test_assist_never_names_a_document_outside_the_gate(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rule 1: a metadata match on a hidden document is not a suggestion."""
    visible = _document(db_session, title="Sigorta Notu A", department=None, text="metin a")
    hidden = _document(db_session, title="Sigorta Gizli Notu", department=None, text="metin b")
    monkeypatch.setattr(retrieval_module, "allowed_document_ids", lambda *_: {visible.id})
    monkeypatch.setattr(ask_module, "allowed_document_ids", lambda *_: {visible.id})

    body = _ask(client, "Sigorta primi nedir?")
    assert fake_llm.requests == []
    ids = {a["document_id"] for a in body["assist"]["available"]}
    assert ids == {str(visible.id)} and str(hidden.id) not in ids


# ---------------------------------------------------------------- chunks retrieved, model declined


def test_insufficient_keeps_a_valid_model_question_and_lists_retrieved_documents(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    doc = _document(
        db_session,
        title="Sigorta Yenileme Bildirimi",
        department=None,
        text="sigorta poliçesi yenilenmiştir",
    )
    fake_llm.replies = [f"{NO_ANSWER_TEXT}\nSORU: {SORU}"]
    body = _ask(client, "Sigorta primi nedir?")

    assert fake_llm.requests[0].system == SYSTEM_PROMPT_ASSIST
    assert body["answered"] is False and body["answer"] == NO_ANSWER_TEXT  # verdict unchanged
    assert body["sources"] == []
    assist = body["assist"]
    assert assist["question"] == SORU
    assert assist["kind"] == "term_mismatch" and assist["unmatched_terms"] == ["primi"]
    assert [a["document_id"] for a in assist["available"]] == [str(doc.id)]
    assert assist["available"][0]["page_number"] == 1
    assert body["warnings"][0]["kind"] == "insufficient_data"

    row = db_session.scalars(select(AuditLog)).one()
    assert row.assist is not None and row.assist["question"] == SORU
    assert row.answer == NO_ANSWER_TEXT


def test_insufficient_drops_a_model_question_that_carries_a_number(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    _document(
        db_session, title="Sigorta Yenileme Bildirimi", department=None, text="sigorta poliçesi"
    )
    fake_llm.replies = [f"{NO_ANSWER_TEXT}\nSORU: 2025 poliçesini mi soruyorsunuz?"]
    body = _ask(client, "Sigorta primi nedir?")
    assist = body["assist"]
    assert assist["question"] == term_mismatch_template(["primi"])  # template fallback
    row = db_session.scalars(select(AuditLog)).one()
    assert row.assist["dropped_reason"] == "contains a number, date, currency or percent"


def test_answered_reply_strips_the_marker_line_and_carries_no_assist(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    _document(
        db_session, title="Sigorta Yenileme Bildirimi", department=None, text="sigorta poliçesi"
    )
    fake_llm.replies = ["Poliçe yenilenmiştir [K1].\nSORU: Başka bir şey mi?"]
    body = _ask(client, "Sigorta poliçesi yenilendi mi?")
    assert body["answered"] is True
    assert body["answer"] == "Poliçe yenilenmiştir [K1]."
    assert body["assist"] is None
    assert db_session.scalars(select(AuditLog)).one().assist is None
