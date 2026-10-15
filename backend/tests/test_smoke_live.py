"""`scripts/smoke_live.py` (İş Emri 2026-10-15A2L): the committed `smoke.json` is valid, the
schema check rejects typos, and the evaluator fails a row for a wrong value / spelling /
behaviour even when the request itself was HTTP 200. No network, no DB."""

from __future__ import annotations

from typing import Any

import pytest

from app.services.ask_router import DATA_PART_HEADING
from scripts import smoke_live
from scripts.smoke_live import DEFAULT_SPEC, evaluate, load_spec, validate_spec, value_segment


def _row(**expect: Any) -> dict[str, Any]:
    return {"letter": "z", "user": "finans", "question": "Soru mu?", "expect": expect}


def _spec(*rows: dict[str, Any]) -> dict[str, Any]:
    return {"version": 1, "questions": list(rows)}


def _body(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "answer": "",
        "answered": True,
        "sources": [],
        "query_type": "DOCUMENT_QUERY",
        "model": "m",
        "tokens_in": 10,
        "tokens_out": 5,
        "assist": None,
    }
    return base | overrides


# ------------------------------------------------------------------ spec


def test_committed_spec_is_valid_and_has_nine_rows() -> None:
    spec = load_spec(DEFAULT_SPEC)
    assert [row["letter"] for row in spec["questions"]] == list("abcdefghi")


def test_data_part_heading_matches_router() -> None:
    assert smoke_live.DATA_PART_HEADING == DATA_PART_HEADING


@pytest.mark.parametrize(
    "bad",
    [
        _row(answerd=True),  # typo
        _row(answered="yes"),  # wrong type
        _row(value="13,600,000"),  # not F-8
        _row(),  # empty expect
        {**_row(answered=True), "user": "nobody"},
    ],
)
def test_validate_spec_rejects(bad: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        validate_spec(_spec(bad))


def test_validate_spec_rejects_duplicate_letters() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        validate_spec(_spec(_row(answered=True), _row(answered=False)))


# ------------------------------------------------------------------ evaluator


def test_http_error_is_the_only_failure() -> None:
    assert evaluate({"answered": True, "value": "1.000"}, 503, {}) == ["http 503"]


def test_value_in_turkish_spelling_passes_and_english_spelling_fails() -> None:
    expect = {"answered": True, "value": "13.600.000 USD"}
    assert evaluate(expect, 200, _body(answer="Tutar 13.600.000 USD'dir [K1].")) == []
    failures = evaluate(expect, 200, _body(answer="Tutar 13,600,000 USD'dir [K1]."))
    assert any(f.startswith("value") for f in failures)
    assert any(f.startswith("F-8") for f in failures)


def test_dates_and_decimal_commas_are_not_english_grouping() -> None:
    body = _body(answer="20.06.2022 tarihli sözleşme, DSCR 1,20x, 13.600.000 USD.")
    assert evaluate({"value": "13.600.000"}, 200, body) == []


def test_mixed_value_must_sit_in_the_excel_part() -> None:
    answer = (
        "Belgelere göre:\nKalan bakiye 11.671.800 USD [K3].\n\n"
        f"{DATA_PART_HEADING}\nKalan banka kredisi bakiyesi 0'dır."
    )
    assert value_segment(answer, "MIXED_QUERY").strip().startswith("Kalan banka")
    failures = evaluate(
        {"value": "11.671.800"}, 200, _body(answer=answer, query_type="MIXED_QUERY")
    )
    assert failures == ["value '11.671.800' not in Excel part"]
    good = answer.replace("0'dır", "11.671.800'dir")
    assert (
        evaluate({"value": "11.671.800"}, 200, _body(answer=good, query_type="MIXED_QUERY")) == []
    )


def test_answered_and_sources_expectations() -> None:
    body = _body(answered=False, sources=[{"title": "x"}])
    failures = evaluate({"answered": True, "sources_min": 2, "sources_empty": True}, 200, body)
    assert failures == [
        "answered=False, expected True",
        "sources=1, expected ≥ 2",
        "sources=1, expected none",
    ]


def test_sources_projects_allows_named_project_and_group_only() -> None:
    sources = [
        {"title": "KZ", "project_code": "IZM_RES", "project_scope": "project"},
        {"title": "Policy", "project_code": None, "project_scope": "group"},
    ]
    assert evaluate({"sources_projects": ["IZM_RES"]}, 200, _body(sources=sources)) == []
    sources.append({"title": "FA", "project_code": "ANK_RES", "project_scope": "project"})
    failures = evaluate({"sources_projects": ["IZM_RES"]}, 200, _body(sources=sources))
    assert failures == ["foreign-project sources: ['ANK_RES:FA']"]


def test_answer_and_response_excludes_are_case_insensitive() -> None:
    body = _body(
        answered=False,
        answer="Bu konuda bilgi bulamadım.",
        assist={
            "kind": "clarify",
            "available": [{"title": "İmar Planı Değişikliği İptali Davası"}],
        },
    )
    expect = {"answer_excludes": ["karatepe"], "response_excludes": ["imar planı değişikliği"]}
    assert evaluate(expect, 200, body) == ["response mentions 'imar planı değişikliği'"]
    assert evaluate({"answer_excludes": ["bulamadım"]}, 200, body) == [
        "answer mentions 'bulamadım'"
    ]


def test_assist_expectations() -> None:
    body = _body(
        answered=False,
        answer="Mevcut şirket kaynaklarında … bulamadım.\nBu adda bir proje kayıtlı değil; "
        "hangi projeyi kastediyorsunuz: Karatepe RES mi, Kızılova RES mi?",
        model=None,
        tokens_in=0,
        tokens_out=0,
        assist={
            "kind": "term_mismatch",
            "question": "Bu adda bir proje kayıtlı değil; hangi projeyi kastediyorsunuz?",
            "unmatched_terms": ["Bursa RES"],
            "available": [],
        },
    )
    expect = {
        "answered": False,
        "assist_kind": "term_mismatch",
        "unmatched_terms": ["Bursa RES"],
        "contains": ["Bu adda bir proje kayıtlı değil"],
        "no_llm": True,
        "single_question": True,
        "question_fact_free": True,
    }
    assert evaluate(expect, 200, body) == []
    llm_body = body | {"model": "claude-haiku-5-5", "tokens_in": 1200}
    assert evaluate({"no_llm": True}, 200, llm_body) == [
        "LLM was called: model='claude-haiku-5-5' tokens=1200/0"
    ]
    wrong_kind = body | {"assist": body["assist"] | {"kind": "clarify", "unmatched_terms": []}}
    assert evaluate(
        {"assist_kind": "term_mismatch", "unmatched_terms": ["Bursa RES"]}, 200, wrong_kind
    ) == [
        "assist.kind='clarify', expected 'term_mismatch'",
        "unmatched_terms=[], expected ['Bursa RES']",
    ]


def test_single_question_and_fact_free_question() -> None:
    body = _body(
        answered=False,
        answer="Bu konuda kesin bilgi bulamadım.\nHangi proje veya sözleşmenin vadesi soruluyor?",
        assist={"kind": "clarify", "question": "Hangi proje veya sözleşmenin vadesi soruluyor?"},
    )
    assert evaluate({"single_question": True, "question_fact_free": True}, 200, body) == []
    two = body | {"answer": body["answer"] + "\nKaratepe RES mi? Boztepe RES mi?"}
    assert evaluate({"single_question": True}, 200, two) == [
        "3 question marks in answer, expected exactly 1"
    ]
    dated = body | {"assist": {"kind": "clarify", "question": "2034 vadesini mi soruyorsunuz?"}}
    assert evaluate({"question_fact_free": True}, 200, dated) == [
        "assist.question carries a fact token: '2034 vadesini mi soruyorsunuz?'"
    ]
    assert evaluate({"single_question": True}, 200, body | {"assist": None}) == [
        "no assist.question"
    ]


def test_no_definition_and_available_min() -> None:
    body = _body(
        answered=False,
        answer="«amendment» ifadesini tadil olarak anladım.\nBu konuda kesin bilgi bulamadım.\n"
        "Elimde konuyla ilgili şunlar var:\n**Karatepe RES:** Amendment 02 (15.03.2025)\n"
        "Genel anlamıyla mı soruyorsunuz?",
        assist={
            "kind": "clarify",
            "question": "Genel anlamıyla mı soruyorsunuz?",
            "available": [{}, {}],
        },
    )
    expect = {"answered": False, "no_definition": True, "assist_available_min": 1}
    assert evaluate(expect, 200, body) == []
    defined = body | {"answer": "Amendment, sözleşme değişikliği anlamına gelir."}
    assert evaluate({"no_definition": True}, 200, defined) == [
        "definition sentence in answer: 'anlamına gel'"
    ]
    assert evaluate({"assist_available_min": 3}, 200, body) == ["assist.available=2, expected ≥ 3"]


def test_render_table_counts_passes() -> None:
    results = [
        smoke_live.RowResult("a", "finans", "q", 200, "DOCUMENT_QUERY", True, 1.0, None),
        smoke_live.RowResult("b", "finans", "q", 200, None, False, 2.0, None, failures=["x"]),
    ]
    table = smoke_live.render_table(results)
    assert "1/2 geçti" in table
    assert "❌ x" in table
