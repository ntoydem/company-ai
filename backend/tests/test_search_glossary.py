"""Domain glossary (Phase 3.2b): Turkish question stems -> English document terms, and the
coverage the golden question set gets from it."""

from __future__ import annotations

from app.services.search_glossary import GLOSSARY, expand_terms
from app.services.search_query import build_search_query, turkish_lower


def test_prefix_match_expands_inflected_turkish_words() -> None:
    extra = expand_terms(["finansmanında", "kredisi"])
    assert "financing" in extra
    assert "loan" in extra
    assert "facility" in extra


def test_multi_word_keys_and_values_become_phrases() -> None:
    extra = expand_terms(["geçici", "kabul", "tarihi"])
    assert '"provisional acceptance"' in extra
    extra = expand_terms(["dscr", "covenant"])
    assert '"debt service coverage"' in extra


def test_no_expansion_for_unknown_words_and_no_duplicates() -> None:
    assert expand_terms(["ankara", "res", "nedir"]) == []
    extra = expand_terms(["kredi", "kredisi", "finansman"])
    assert len(extra) == len(set(extra))
    assert "financing" not in expand_terms(["financing"])  # already a question term


def test_reverse_direction_english_question_turkish_document() -> None:
    assert "lisans" in expand_terms(["licence", "date"])
    assert "çed" in expand_terms(["eia", "status"])


def test_glossary_keys_are_lowercase_stems() -> None:
    for key in GLOSSARY:
        assert key == turkish_lower(key)


def test_built_query_contains_english_terms_for_a_turkish_finance_question() -> None:
    query = build_search_query("Ankara RES'in toplam finansman (kredi) tutarı nedir?")
    for term in ("financing", "facility", "loan", "amount"):
        assert term in query.split(" OR ")
