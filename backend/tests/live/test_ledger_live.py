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
from app.services.answer_prompt import NO_ANSWER_TEXT, NO_REASON_TEXT
from app.services.search_query import turkish_lower
from tests.ledger_fixtures import ledger_value, load_ledger_documents

pytestmark = pytest.mark.live_llm

_TURKISH_CHARS = re.compile(r"[çğıöşüÇĞİÖŞÜ]")
_ENGLISH_WORDS = re.compile(r"\b(the|is|are|was|were|shall)\b")

_FACILITY_REF, _AMENDMENT_REF = "DOC-ANK-FIN-004", "DOC-ANK-FIN-005"
_LICENCE_REF, _LICENCE_AMENDMENT_REF = "DOC-ANK-DEV-001", "DOC-ANK-DEV-002"


@pytest.fixture(autouse=True)
def _require_live(settings: Settings) -> None:
    if os.environ.get("LLM_LIVE_TESTS") != "1":
        pytest.skip("LLM_LIVE_TESTS=1 not set")
    if not (settings.llm_api_key and settings.llm_api_key.get_secret_value()):
        pytest.skip("LLM_API_KEY not set")


# Gemini free tier: 5 requests / minute per model. Since Phase 4.3 one `/api/ask` is two
# LLM requests (router + answer, same model in `.env`), so space calls ~26 s apart and, on
# a 503 (rate limit mapped by the API), wait for the window to reset and try once more.
_CALL_SPACING_S = 26
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


def _ratio_aliases(value: float) -> tuple[str, str, str, str]:
    """Both the exact 2-decimal form `_format_ratio()` actually renders into the source
    document ("1,20x" — never stripped, see `seed_data/generator/facts.py`) and a
    trailing-zero-stripped form ("1,2x"), in case the model normalizes it despite rule 7
    asking it to keep the source's own formatting."""
    exact = f"{value:.2f}"
    stripped = exact.rstrip("0").rstrip(".")
    return (
        f"{exact.replace('.', ',')}x",
        f"{exact}x",
        f"{stripped.replace('.', ',')}x",
        f"{stripped}x",
    )


def _value_in(answer: str, *aliases: str) -> bool:
    return any(alias in answer for alias in aliases)


def _number_aliases(value: float, unit: str) -> tuple[str, str]:
    text = str(int(value)) if float(value).is_integer() else f"{value:.1f}"
    comma = text.replace(".", ",")
    return f"{text} {unit}", f"{comma} {unit}"


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


def test_current_tenor_vs_initial_facility_tenor_differ(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    """Phase 3.2 kabul kriteri: "güncel X" ↔ "ilk X" farklı ve doğru — T1 doğrulaması
    (docs/plans/PHASE_3_2_PLAN.md): ADR-021'in genel zincir mekanizması, DSCR dışında,
    aynı Facility zincirindeki başka bir alanda (vade/tenor) da doğru çalışıyor. Not:
    Licence → Licence Amendment 01 çifti bu doğrulama için kullanılamıyor — o iki belge
    kasıtlı olarak `supersedes` değil `related_document_ids` ile bağlı
    (`test_licence_amendment_is_related_not_superseding`, Phase 3.1), yani chain tabanlı
    GÜNCEL/İLK HALKA ayrımına hiç girmiyor; bu Facility zinciri (gerçek `supersedes`
    ilişkisi) bu yüzden tercih edildi."""
    load_ledger_documents(db_session, [_FACILITY_REF, _AMENDMENT_REF])
    initial = ledger_value("ankara_res.project.finance.tenor_years.initial.value")
    current = ledger_value("ankara_res.project.finance.tenor_years.current.value")
    assert initial != current

    current_body = _ask(client, "Ankara RES Facility Agreement'ının güncel vadesi kaç yıldır?")
    initial_body = _ask(client, "Ankara RES Facility Agreement'ının ilk vadesi kaç yıldı?")

    assert current_body["answered"] is True and initial_body["answered"] is True
    current_answer = str(current_body["answer"])
    initial_answer = str(initial_body["answer"])
    assert _value_in(
        current_answer, *_number_aliases(current, "yıl"), *_number_aliases(current, "years")
    )
    assert _value_in(
        initial_answer, *_number_aliases(initial, "yıl"), *_number_aliases(initial, "years")
    )
    assert current_answer != initial_answer
    _assert_turkish(current_answer)
    _assert_turkish(initial_answer)


def test_why_question_without_stated_reason_returns_fixed_text(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    """Phase 3.2 kabul kriteri: "EBITDA neden düştü?" → yalnızca belgede yazan sebep veya
    "belirtilmemiş" (kural 6) — T2 doğrulaması: Facility Agreement Amendment 01'in metni
    DSCR/vade değerlerini *değiştirir* ama *neden* değiştirdiğini hiç açıklamaz (bkz.
    prose/DOC-ANK-FIN-005.yaml — yalnızca "the parties hereby agree to modify..." der,
    gerekçe içermez); bu yüzden gerçek bir "neden?" sorusu sabit metni dönmeli. (Not:
    DOC-ANK-DEV-002/Licence Amendment 01'in kendi "Tadil Gerekçesi" bölümü *vardır* — o
    belge için aynı soru doğru şekilde o bölümü aktarır, "belirtilmemiş" demez; kural 6
    her iki dalı da doğru uyguluyor, bu test yalnızca "sebepsiz" dalı kanıtlıyor.)"""
    load_ledger_documents(db_session, [_FACILITY_REF, _AMENDMENT_REF])
    body = _ask(client, "Ankara RES'in güncel minimum DSCR covenant'ı neden değiştirildi?")
    answer = str(body["answer"])
    assert body["answered"] is True, "kaynak bulundu, yalnızca sebep belirtilmemiş olmalı"
    # Case-insensitive: a sentence-initial "Belgelerde..." is expected, not a mismatch.
    assert NO_REASON_TEXT in turkish_lower(answer)
    _assert_turkish(answer)


def test_value_stated_only_in_a_superseded_chain_member_is_still_answered(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    """Phase 3.2b root cause: Amendment 01 supersedes the Facility Agreement but restates
    none of the unchanged terms (the loan amount lives only in the superseded base). Rule 5
    used to make the model base itself on the GÜNCEL document alone and refuse — 0/18 in the
    Phase 3.2b consistency baseline. An amendment only changes what it states."""
    load_ledger_documents(db_session, [_FACILITY_REF, _AMENDMENT_REF])
    total_debt = ledger_value("ankara_res.project.finance.total_debt.value")

    body = _ask(client, "Ankara RES'in toplam finansman (kredi) tutarı nedir?")

    assert body["answered"] is True, body["answer"]
    answer = str(body["answer"])
    grouped_en = f"{int(total_debt):,}"
    grouped_tr = grouped_en.replace(",", ".")
    assert grouped_en in answer or grouped_tr in answer, answer
    titles = {source["title"] for source in body["sources"]}
    assert "Facility Agreement" in titles
    _assert_turkish(answer)


def test_excel_dscr_question_is_planned_computed_and_cited(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    """Phase 4.2 kabul kriteri: "Ankara RES 2026 Q2 DSCR kaç?" -> the real planning model
    picks `dscr(Q2_2026)` (or an equivalent SELECT), DuckDB/openpyxl computes, the cited
    range is `Covenant_Report.xlsx Q2_2026!D14` and the phrased answer carries the value."""
    from pathlib import Path

    excel_dir = Path(__file__).resolve().parents[2] / "seed_data" / "excel"
    response = client.post(
        "/api/documents/upload",
        files={
            "file": (
                "Covenant_Report.xlsx",
                (excel_dir / "Covenant_Report.xlsx").read_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={
            "title": "Covenant Report (workbook)",
            "document_type": "Covenant Report",
            "document_date": "2026-08-15",
            "counterparty": "PQR Bank",
        },
    )
    assert response.status_code == 201, response.text
    time.sleep(_CALL_SPACING_S)
    answer = client.post("/api/excel/ask", json={"question": "Ankara RES 2026 Q2 DSCR kaç?"})
    assert answer.status_code == 200, answer.text
    body = answer.json()
    print(f"\nPLAN: {body['plan']}\nCEVAP: {body['answer']}\nKAYNAK: {body['sources']}")
    expected = ledger_value("ankara_res.project.finance.covenant_tests[-1].dscr")
    assert body["answered"] is True
    assert body["value"] == expected
    assert body["sources"][0]["label"] == "Covenant_Report.xlsx Q2_2026!D14"
    assert body["formatted_value"] in body["answer"]
    _assert_turkish(str(body["answer"]))
