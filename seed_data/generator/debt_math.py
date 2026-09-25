"""Facility debt arithmetic shared by the ledger validator (F9-F11), `generate_excel.py`
and `validate_excel.py` (Phase 4.2). Pure functions over ledger values — one place, so the
workbook formulas, the validator and the demo answers cannot drift apart.

Conventions (docs/plans/PHASE_4_2_PLAN.md §1): semi-annual periods `H1_YYYY` (ends 30 Jun)
and `H2_YYYY` (ends 31 Dec); interest for a half = opening balance × (base + margin) / 2,
drawdowns made during a half start accruing in the next half; quarterly debt service =
half of the semi-annual (principal + interest) of the half containing the quarter.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class HalfYear:
    period: str  # H1_2024
    end: date

    @property
    def year(self) -> int:
        return self.end.year


@dataclass(frozen=True)
class ScheduleRow:
    period: str
    end: date
    opening: float
    drawdown: float
    principal: float
    rate_pct: float  # base + margin
    interest: float
    closing: float

    @property
    def debt_service(self) -> float:
        return self.principal + self.interest


def half_years(first: date, last: date) -> list[HalfYear]:
    rows: list[HalfYear] = []
    year, second = first.year, first.month > 6
    while True:
        end = date(year, 12, 31) if second else date(year, 6, 30)
        rows.append(HalfYear(f"H{2 if second else 1}_{year}", end))
        if end >= last:
            return rows
        if second:
            year += 1
        second = not second


def half_of(day: date) -> str:
    return f"H{2 if day.month > 6 else 1}_{day.year}"


def half_of_quarter(period: str) -> str:
    """`Q3_2025` -> `H2_2025`."""
    quarter, year = period.split("_")
    return f"H{1 if quarter in ('Q1', 'Q2') else 2}_{year}"


def build_schedule(
    *,
    drawdowns: list[tuple[date, float]],
    instalments: list[tuple[date, float]],
    base_rate_pct_by_year: dict[int, float],
    margin_pct: float,
) -> list[ScheduleRow]:
    """Every half from the first drawdown's half to the last instalment's half."""
    first = min(d for d, _ in drawdowns)
    last = max(d for d, _ in instalments)
    draw_by_half: dict[str, float] = {}
    for day, amount in drawdowns:
        draw_by_half[half_of(day)] = draw_by_half.get(half_of(day), 0.0) + amount
    principal_by_half: dict[str, float] = {}
    for day, amount in instalments:
        principal_by_half[half_of(day)] = principal_by_half.get(half_of(day), 0.0) + amount

    rows: list[ScheduleRow] = []
    balance = 0.0
    for half in half_years(first, last):
        opening = balance
        drawdown = draw_by_half.get(half.period, 0.0)
        principal = principal_by_half.get(half.period, 0.0)
        rate = base_rate_pct_by_year[half.year] + margin_pct
        interest = round(opening * rate / 100 / 2, 2)
        closing = opening + drawdown - principal
        rows.append(
            ScheduleRow(
                half.period, half.end, opening, drawdown, principal, rate, interest, closing
            )
        )
        balance = closing
    return rows


def outstanding_on(rows: list[ScheduleRow], day: date) -> float:
    """Closing balance of the last half that ended on or before `day`."""
    closed = [r for r in rows if r.end <= day]
    return closed[-1].closing if closed else 0.0


def quarterly_debt_service(rows: list[ScheduleRow], quarter: str) -> float:
    by_period = {r.period: r for r in rows}
    return by_period[half_of_quarter(quarter)].debt_service / 2
