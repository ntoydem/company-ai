"""Ek-F F-8 (ADR-030): Turkish formatting by code — never a rounding, never a clock time."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from app.services import tr_format as t


def test_numbers_group_thousands_and_keep_their_own_decimals() -> None:
    assert t.format_number(72000000) == "72.000.000"
    assert t.format_number(1234567.89) == "1.234.567,89"
    assert t.format_number(Decimal("1000.5")) == "1.000,5"
    assert t.format_number(-2500) == "-2.500"
    assert t.format_number(0) == "0"
    assert t.format_number(999) == "999"


def test_amounts_carry_the_currency_code_after_the_number() -> None:
    assert t.format_amount(44100000, "EUR") == "44.100.000 EUR"
    assert t.format_amount(1234567.89, "USD") == "1.234.567,89 USD"
    assert t.format_amount(18989.44, "TRY") == "18.989,44 TL"
    assert t.format_amount(100, "€") == "100 EUR"
    assert t.format_amount(100, None) == "100"


def test_percent_has_at_least_two_decimals_and_never_rounds() -> None:
    # Naci SORU 2 (09.10.2026): ≥ 2 decimals, more kept when the value carries them.
    assert t.format_percent(2.9) == "%2,90"
    assert t.format_percent(12.5) == "%12,50"
    assert t.format_percent(38.2) == "%38,20"
    assert t.format_percent(3.89378) == "%3,89378"  # cutting to 4 would change the value
    assert t.format_percent(Decimal("1.2345")) == "%1,2345"
    assert t.format_percent(20) == "%20,00"


def test_multiples_have_two_decimals() -> None:
    assert t.format_multiple(1.2) == "1,20x"
    assert t.format_multiple(1.37) == "1,37x"
    assert t.format_multiple(Decimal("1.255")) == "1,255x"


def test_dates_are_gg_aa_yyyy_without_a_clock() -> None:
    assert t.format_date(date(2021, 11, 15)) == "15.11.2021"
    assert t.format_date(datetime(2021, 11, 15, 0, 0)) == "15.11.2021"
    assert t.format_date(datetime(2026, 10, 7, 14, 30)) == "07.10.2026"


def test_unit_is_read_from_the_column_label() -> None:
    assert t.unit_from_label("Capex (EUR)") == "EUR"
    assert t.unit_from_label("Cash to equity (EUR)") == "EUR"
    assert t.unit_from_label("Share (%)") == "%"
    assert t.unit_from_label("Energy (MWh)") == "MWh"
    assert t.unit_from_label("DSCR") == "x"
    assert t.unit_from_label("Financial close") is None
    assert t.unit_from_label(None) is None


def test_format_value_and_cell_cover_every_engine_type() -> None:
    assert t.format_value(44100000, "EUR") == "44.100.000 EUR"
    assert t.format_value(1.37, "x") == "1,37x"
    assert t.format_value(38.2, "%") == "%38,20"
    assert t.format_value(108858, "MWh") == "108.858 MWh"
    assert t.format_value(1000000, "") == "1.000.000"
    assert t.format_value(None, "EUR") == "-"
    assert t.format_value("text", "EUR") == "text"
    assert t.format_value(datetime(2021, 11, 15), None) == "15.11.2021"
    assert t.format_cell(72000000.0, "Capex (EUR)") == "72.000.000 EUR"
    assert t.format_cell(datetime(2021, 11, 15, 0, 0), "Financial close") == "15.11.2021"
    assert t.format_cell(1000000.0, "Repayment") == "1.000.000"  # no unit → no invented code


def test_polish_answer_rewrites_dates_and_english_numbers_only() -> None:
    text = (
        "Kapanış 2021-11-15 00:00:00 tarihinde [K1]; tutar 1,234,567.89 EUR [K12]. "
        "Sözleşme S-26-001, fatura ENR2026001121, 2026 yılı, 44.100.000 EUR, 1,20x, "
        "vade 07.04.2027 00:00."
    )
    out = t.polish_answer(text)
    assert "15.11.2021 tarihinde [K1]" in out
    assert "1.234.567,89 EUR [K12]" in out
    assert "vade 07.04.2027." in out
    # untouched: labels, document numbers, years, already-Turkish spellings
    assert "S-26-001" in out and "ENR2026001121" in out and "2026 yılı" in out
    assert "44.100.000 EUR" in out and "1,20x" in out
    assert t.polish_answer("1.37x ve 1234567") == "1.37x ve 1234567"  # no grouping by guess
    assert t.polish_answer("2021-13-45") == "2021-13-45"  # not a date, left alone
