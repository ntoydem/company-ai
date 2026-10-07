"""Pure parts of `scripts/validate_ocr.py` (quality gate (c), 07.10.2026): page lookup from
the prose tokens and the format-insensitive fact comparison. The DB-backed run itself is
`make validate-ocr` (needs ingested documents — not part of `make test`/`make lint`)."""

from __future__ import annotations

from scripts.validate_ocr import check_entry, compare_fact, expected_pages

PROSE = {
    "sections": [
        {"heading": "Karar Gerekçesi", "paragraphs": ["[[spv_name]] ile [[counterparty]] …"]},
        {"heading": "Alınan Karar", "paragraphs": ["… [[ghi_share_pct]] oranındaki hisse devri …"]},
    ]
}
PAGE_MAP = {"cover": 1, "Karar Gerekçesi": 2, "Alınan Karar": 3, "__signatures__": 4}


def test_expected_pages_follow_the_prose_token() -> None:
    assert expected_pages(PROSE, PAGE_MAP, "ghi_share_pct") == (3,)
    assert expected_pages(PROSE, PAGE_MAP, "spv_name") == (2,)
    assert expected_pages(PROSE, PAGE_MAP, "document_date") == ()  # cover-only fact


def test_compare_fact_is_format_insensitive_for_numbers_dates_and_money() -> None:
    assert compare_fact("%20", "… yüzde 20 oranındaki hisse devri …")[0]
    assert compare_fact("yüzde 20", "… %20 oranındaki …")[0]
    assert compare_fact("15.11.2021", "finansal kapanış 15 Kasım 2021 tarihinde")[0]
    assert compare_fact("45.000.000 EUR", "a facility of 45,000,000 EUR")[0]
    assert compare_fact("1,25x", "DSCR covenant 1.25x minimum")[0]
    ok, detail = compare_fact("%20", "… 9020 oranındaki hisse devri …")
    assert not ok and "9020" in detail


def test_compare_fact_text_values_are_folded_substrings() -> None:
    assert compare_fact("devam ediyor", "ÇED süreci DEVAM  EDİYOR.")[0]  # case + Turkish İ
    assert compare_fact("sculpted", "the repayment profile is Sculpted")[0]
    assert not compare_fact("annuity", "the repayment profile is sculpted")[0]


def test_check_entry_searches_the_token_pages_then_falls_back_to_all() -> None:
    entry = {
        "external_ref": "DOC-X",
        "page_map": PAGE_MAP,
        "key_facts_used": {"ghi_share_pct": "%20", "document_date": "01.05.2021"},
    }
    pages = {1: "Tarih: 01.05.2021", 2: "gerekçe", 3: "… 9020 oranındaki …", 4: "imza"}
    results = {r.field: r for r in check_entry(entry, pages, PROSE)}
    assert results["ghi_share_pct"].pages == (3,) and not results["ghi_share_pct"].ok
    assert results["document_date"].pages == (1, 2, 3, 4) and results["document_date"].ok
