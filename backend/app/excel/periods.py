"""Period normalisation for Excel questions: Turkish/English spellings of a quarter,
month or year to the ledger/workbook keys (`Q2_2026`, `2026-06`, `2026`)."""

from __future__ import annotations

import re

_QUARTER_WORDS = {
    "1": "Q1",
    "2": "Q2",
    "3": "Q3",
    "4": "Q4",
    "i": "Q1",
    "ii": "Q2",
    "iii": "Q3",
    "iv": "Q4",
}
_QUARTER = re.compile(
    r"(?:(?P<y1>20\d{2})\D{0,6}q(?P<q1>[1-4])\b)"
    r"|(?:(?P<y4>20\d{2})\D{0,8}(?P<q4>[1-4])(?:\.|'?inci|'?nci|'?üncü|'?ncü)?\s*çeyre)"
    r"|(?:q(?P<q2>[1-4])[\s_/-]*(?P<y2>20\d{2}))"
    r"|(?:(?P<q3>[1-4])\.?\s*çeyrek\D{0,6}(?P<y3>20\d{2}))",
    re.IGNORECASE,
)
_MONTH = re.compile(r"\b(?P<y>20\d{2})[-/.](?P<m>0[1-9]|1[0-2])\b")
_YEAR = re.compile(r"\b(?P<y>20\d{2})\b")


def normalize_quarter(text: str) -> str | None:
    """`"2026 Q2"`, `"Q2 2026"`, `"2026 2. çeyrek"`, `"Q2_2026"` -> `"Q2_2026"`."""
    match = _QUARTER.search(text)
    if match is None:
        return None
    g = match.groupdict()
    for q, y in (("q1", "y1"), ("q4", "y4"), ("q2", "y2"), ("q3", "y3")):
        if g.get(q) and g.get(y):
            return f"{_QUARTER_WORDS[g[q].lower()]}_{g[y]}"
    return None


def normalize_month(text: str) -> str | None:
    match = _MONTH.search(text)
    return f"{match.group('y')}-{match.group('m')}" if match else None


def normalize_year(text: str) -> str | None:
    match = _YEAR.search(text)
    return match.group("y") if match else None


def normalize_period(text: str) -> str | None:
    """Most specific first: quarter, then month, then year; `None` when nothing matches."""
    return normalize_quarter(text) or normalize_month(text) or normalize_year(text)
