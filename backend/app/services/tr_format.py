"""Turkish number/date formatting by code (Ek-F F-8, ADR-030).

Dates `GG.AA.YYYY` (never a clock time), numbers `1.234.567,89`, currency code after the
amount (`1.234.567,89 USD`), percentages `%2,90`, multiples `1,20x`. **Nothing here rounds a
value**: a percentage keeps every significant decimal it came with (at least two, at most
four — Naci SORU 2, 09.10.2026); a plain number keeps its own decimals. The model never
formats — these helpers run on the engine's values (Excel path) and on the finished answer
text (document path, dates and English number spellings only — SORU 8).
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

CURRENCY_CODES: dict[str, str] = {
    "TRY": "TL",
    "TL": "TL",
    "₺": "TL",
    "USD": "USD",
    "$": "USD",
    "EUR": "EUR",
    "€": "EUR",
}
_UNIT_IN_LABEL = re.compile(r"\(([^()]+)\)\s*$")
_ISO_DATETIME = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})(?:[ T]00:00(?::00)?(?:\.0+)?)?\b")
_TR_DATE_WITH_MIDNIGHT = re.compile(r"\b(\d{2}\.\d{2}\.\d{4}) 00:00(?::00)?\b")
# English thousands grouping with an optional decimal point: 1,234,567.89 / 1,234,567.
# Requires at least one comma group so a plain decimal ("1.37") is left alone.
_EN_NUMBER = re.compile(r"(?<![\w.,])(\d{1,3}(?:,\d{3})+)(?:\.(\d+))?(?![\w,])")


def _decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise TypeError("bool is not a number")
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        # repr() is the shortest round-tripping spelling — the value itself, not a rounding.
        return Decimal(repr(value))
    return Decimal(str(value))


def _group_thousands(integer_part: str) -> str:
    sign = "-" if integer_part.startswith("-") else ""
    digits = integer_part.lstrip("-")
    groups: list[str] = []
    while digits:
        groups.insert(0, digits[-3:])
        digits = digits[:-3]
    return sign + ".".join(groups)


def format_number(value: Any, *, min_decimals: int = 0, max_decimals: int | None = None) -> str:
    """`1.234.567,89`. Decimals are the value's own (trailing zeros dropped), padded up to
    `min_decimals`, and never cut below the value's significant digits unless `max_decimals`
    is given — in which case digits beyond it are kept anyway if cutting would change the
    value (no rounding, ever)."""
    number = _decimal(value)
    text = format(number, "f")
    integer_part, _, fraction = text.partition(".")
    fraction = fraction.rstrip("0")
    if max_decimals is not None and len(fraction) > max_decimals:
        if fraction[max_decimals:].strip("0"):
            pass  # cutting would change the value: keep every digit
        else:
            fraction = fraction[:max_decimals]
    if len(fraction) < min_decimals:
        fraction = fraction + "0" * (min_decimals - len(fraction))
    grouped = _group_thousands(integer_part)
    return f"{grouped},{fraction}" if fraction else grouped


def normalize_currency(code: str | None) -> str | None:
    if code is None:
        return None
    return CURRENCY_CODES.get(code.strip().upper(), CURRENCY_CODES.get(code.strip()))


def format_amount(value: Any, currency: str | None) -> str:
    """`44.100.000 EUR` — code after the amount; no code when the unit is not a currency."""
    code = normalize_currency(currency)
    text = format_number(value)
    return f"{text} {code}" if code else text


def format_percent(value: Any) -> str:
    """`%2,90`, `%12,50`, `%38,2` → `%38,20`; `%3,89378` keeps its digits (max 4 → kept
    anyway because cutting would change the value)."""
    return "%" + format_number(value, min_decimals=2, max_decimals=4)


def format_multiple(value: Any) -> str:
    """`1,20x` (two decimals, more only if the value carries them)."""
    return format_number(value, min_decimals=2, max_decimals=4) + "x"


def format_date(value: date | datetime) -> str:
    """`GG.AA.YYYY`; a datetime loses its clock (Ek-F has no times)."""
    return value.strftime("%d.%m.%Y")


def unit_from_label(label: str | None) -> str | None:
    """`"Capex (EUR)"` → `EUR`, `"Share (%)"` → `%`, `"DSCR"` → `x`, `"Energy (MWh)"` →
    `MWh`; `None` when the label says nothing."""
    if not label:
        return None
    match = _UNIT_IN_LABEL.search(label.strip())
    if match:
        return match.group(1).strip()
    if label.strip().upper() in {"DSCR", "LLCR", "PLCR"}:
        return "x"
    return None


def format_value(value: Any, unit: str | None) -> str:
    """One engine value with its unit: currency → amount + code, `%` → percent, `x` →
    multiple, other units appended (`108.858 MWh`), no unit → bare number. Strings, dates
    and None pass through their own rule."""
    if value is None:
        return "-"
    if isinstance(value, datetime | date):
        return format_date(value)
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return str(value)
    unit = (unit or "").strip()
    if unit == "x":
        return format_multiple(value)
    if unit == "%":
        return format_percent(value)
    code = normalize_currency(unit) if unit else None
    if code:
        return format_amount(value, code)
    text = format_number(value)
    return f"{text} {unit}" if unit else text


def format_cell(value: Any, column_label: str | None) -> str:
    """A table cell on the Excel path: the unit is read from the column label."""
    return format_value(value, unit_from_label(column_label))


def polish_answer(text: str) -> str:
    """Document-path gate (SORU 8: dates and English number spellings only). ISO dates and
    midnight timestamps become `GG.AA.YYYY`; `1,234,567.89` becomes `1.234.567,89`.
    Citation labels, document numbers, years and ungrouped digit runs are left alone."""

    def iso(match: re.Match[str]) -> str:
        y, m, d = match.group(1), match.group(2), match.group(3)
        try:
            return date(int(y), int(m), int(d)).strftime("%d.%m.%Y")
        except ValueError:
            return match.group(0)

    def english(match: re.Match[str]) -> str:
        grouped = match.group(1).replace(",", ".")
        return f"{grouped},{match.group(2)}" if match.group(2) else grouped

    text = _ISO_DATETIME.sub(iso, text)
    text = _TR_DATE_WITH_MIDNIGHT.sub(r"\1", text)
    return _EN_NUMBER.sub(english, text)
