"""Adım 2 (Tansu Ürün 1 §B; `docs/plans/ADIM2_PLAN.md`): D1 workbooks reach "elimde şunlar
var", D2 concept glossary in the metadata search, D3 generic question words, D4 acronym
probes, D5 existence questions always list — all inside `allowed_document_ids` (G3)."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.document import Document, DocumentStatus, IngestionStatus
from app.models.user import User
from app.services import ask as ask_module
from app.services import retrieval as retrieval_module
from app.services.answer_prompt import NO_ANSWER_TEXT
from app.services.assist import (
    GENERIC_TERMS,
    available_from_metadata,
    is_existence_question,
    mismatch_terms,
    unmatched_terms,
)
from app.services.search_glossary import concept_matches, metadata_terms
from tests.fakes import FakeLLMClient
from tests.test_ask import _ask, _document


@pytest.fixture
def assist_on(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "assist_mode_enabled", True)


def _workbook(
    session: Session, *, title: str, document_type: str, department: str | None
) -> Document:
    """A ready xlsx document: no chunks, so it can only be found through metadata."""
    document = Document(
        title=title,
        document_type=document_type,
        counterparty="c",
        document_date=date(2026, 1, 1),
        status=DocumentStatus.executed,
        storage_path=f"{uuid.uuid4()}/original.xlsx",
        department=department,
        ingestion_status=IngestionStatus.ready,
    )
    session.add(document)
    session.commit()
    return document


# ---------------------------------------------------------------- pure helpers


def test_concept_glossary_maps_turkish_concepts_to_title_words() -> None:
    assert "Financial Model" in metadata_terms(["ankara'nın", "finansal", "modeli"])
    assert "Financial Model" in metadata_terms(["ödeme", "planı", "yüklü"])
    assert "Budget" in metadata_terms(["bütçe", "dosyası"])
    assert metadata_terms(["kapasite", "kaç"]) == []
    covered = dict(concept_matches(["finansal", "modeli", "var"]))
    assert any("finansal" in tokens for tokens in covered)


def test_generic_terms_cover_question_verbs_and_fillers() -> None:
    for word in ("bitiyor", "demek", "biliyor", "musun", "yüklü", "dosyası", "nerede", "neler"):
        assert word in GENERIC_TERMS
    assert mismatch_terms(["bitiyor", "demek", "biliyor", "musun"]) == []


def test_existence_question_patterns() -> None:
    assert is_existence_question("Ankara'nın finansal modeli var mı?")
    assert is_existence_question("Ödeme planı yüklü mü?")
    assert is_existence_question("ÇED raporu nerede?")
    assert is_existence_question("Teminat belgeleri neler?")
    assert not is_existence_question("Kredi sözleşmesinin vadesi kaç yıl?")


# ---------------------------------------------------------------- metadata lookups (DB)


def test_metadata_finds_an_english_workbook_from_a_turkish_concept(
    db_session: Session, admin_user: User
) -> None:
    wb = _workbook(
        db_session, title="Financial Model 2026", document_type="Financial Model", department=None
    )
    other = _document(db_session, title="Facility Agreement", department=None, text="DSCR covenant")
    allowed = {wb.id, other.id}
    terms = ["Ankara'nın", "finansal", "modeli"]
    cards = available_from_metadata(db_session, allowed, terms)
    assert [c.document_id for c in cards] == [wb.id]
    # D2: "finansal"/"modeli" are not missing words — their concept exists in the titles
    # ("Ankara" is unmatched here only because this tiny corpus has no Ankara document).
    assert set(unmatched_terms(db_session, allowed, terms)) <= {"Ankara'nın"}


def test_metadata_acronym_probe_reaches_short_turkish_acronyms(
    db_session: Session, admin_user: User
) -> None:
    ced = _document(
        db_session, title="Ankara RES ÇED Olumlu Kararı", department=None, text="çevresel etki"
    )
    _document(db_session, title="Facility Agreement", department=None, text="loan")
    cards = available_from_metadata(db_session, {ced.id}, ["ÇED", "raporu", "nerede"])
    assert [c.document_id for c in cards] == [ced.id]


def test_metadata_never_lists_a_document_outside_allowed(
    db_session: Session, admin_user: User
) -> None:
    visible = _workbook(
        db_session,
        title="Budget vs Actual 2026",
        document_type="Budget vs Actual",
        department="enerji_grubu",
    )
    hidden = _workbook(
        db_session,
        title="Financial Model 2026",
        document_type="Financial Model",
        department="finans",
    )
    cards = available_from_metadata(db_session, {visible.id}, ["bütçe", "finansal", "modeli"])
    assert [c.document_id for c in cards] == [visible.id]
    assert hidden.id not in {c.document_id for c in cards}


# ---------------------------------------------------------------- /api/ask paths


def test_existence_question_lists_the_workbook_when_the_model_declines(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    """D1/D5: chunks came from a contract, the model said no; the workbook has no chunks but
    its title matches the concept — it must be in "elimde şunlar var" with a question."""
    wb = _workbook(
        db_session, title="Financial Model 2026", document_type="Financial Model", department=None
    )
    _document(
        db_session, title="Facility Agreement", department=None, text="ödeme planı yıllık taksit"
    )
    fake_llm.replies = [NO_ANSWER_TEXT]

    body = _ask(client, "Ödeme planı yüklü mü?")

    assert body["answered"] is False and body["answer"] == NO_ANSWER_TEXT
    assist = body["assist"]
    assert assist["kind"] == "clarify"  # "yüklü"/"planı" no longer count as unknown terms
    assert str(wb.id) in {a["document_id"] for a in assist["available"]}
    assert assist["question"]


def test_zero_chunk_existence_question_lists_the_workbook(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    wb = _workbook(
        db_session, title="Financial Model 2026", document_type="Financial Model", department=None
    )
    body = _ask(client, "Finansal model var mı?")
    assert fake_llm.requests == []  # zero chunks: still no LLM (ADR-021)
    assert [a["document_id"] for a in body["assist"]["available"]] == [str(wb.id)]
    assert body["assist"]["kind"] == "clarify"


def test_hidden_workbook_is_never_named(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """G3: a restricted workbook outside the gate does not appear in the list, nor its title
    anywhere in the response."""
    hidden = _workbook(
        db_session, title="Financial Model 2026", document_type="Financial Model", department=None
    )
    visible = _document(
        db_session, title="Facility Agreement", department=None, text="DSCR covenant"
    )
    monkeypatch.setattr(retrieval_module, "allowed_document_ids", lambda *_: {visible.id})
    monkeypatch.setattr(ask_module, "allowed_document_ids", lambda *_: {visible.id})
    fake_llm.replies = [NO_ANSWER_TEXT]

    body = _ask(client, "Finansal model var mı?")

    ids = {a["document_id"] for a in (body["assist"] or {}).get("available", [])}
    assert str(hidden.id) not in ids
    assert "Financial Model" not in str(body)
