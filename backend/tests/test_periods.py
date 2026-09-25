from __future__ import annotations

import pytest

from app.excel.periods import normalize_month, normalize_period, normalize_quarter, normalize_year


@pytest.mark.parametrize(
    "text",
    [
        "2026 Q2",
        "Q2 2026",
        "Q2_2026",
        "2026 2. çeyrek",
        "2026'nın 2. çeyreği",
        "2. çeyrek 2026",
        "q2/2026",
    ],
)
def test_quarter_spellings(text: str) -> None:
    assert normalize_quarter(text) == "Q2_2026"


def test_month_and_year() -> None:
    assert normalize_month("2026-06 üretimi") == "2026-06"
    assert normalize_year("2026 toplam üretim") == "2026"
    assert normalize_period("Ankara RES 2026 Q2 DSCR kaç?") == "Q2_2026"
    assert normalize_period("2025-12 kaç MWh?") == "2025-12"
    assert normalize_period("2025 yılı") == "2025"
    assert normalize_period("DSCR kaç?") is None
