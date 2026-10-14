"""İş Emri 2026-10-14S2c (B2-b §4c): a planned SELECT that picked ONE row dated after
TODAY is a projection, not a current value. The engine identifies the row the scalar
result came from (the value sits in a column the SQL names, and only in rows whose date
column is after TODAY) and the pipeline re-plans once with a feedback line — unless the
plan says `"future_ok": true` (the question explicitly asked a future period).
Deterministic, no model involved; a value that also occurs in a past row is left alone."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import polars as pl

from app.excel.calc import ROW_COLUMN, LoadedWorkbook
from app.excel.sql_guard import SqlRejectedError, guard_select

_DATE_TYPES = (pl.Date, pl.Datetime)
_PREFERRED_DATE_COLUMNS = ("end_date", "quarter_end", "date")


@dataclass(frozen=True)
class FutureRow:
    """The selected row, described for the retry feedback without any cell *figure*:
    the table, its date column, the Excel row number and the row's label (first string
    cell, as `candidate_labels` does)."""

    table: str
    date_column: str
    excel_row: int
    label: str | None


def _date_column(frame: pl.DataFrame) -> str | None:
    dated = [
        c for c in frame.columns if c != ROW_COLUMN and isinstance(frame.schema[c], _DATE_TYPES)
    ]
    if not dated:
        return None
    for preferred in _PREFERRED_DATE_COLUMNS:
        if preferred in dated:
            return preferred
    return dated[0]


def _named_in(sql: str, column: str) -> bool:
    return re.search(rf"(?<![a-z0-9_]){re.escape(column)}(?![a-z0-9_])", sql.lower()) is not None


def _to_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return None


def _matching_rows(frame: pl.DataFrame, column: str, value: Any) -> pl.DataFrame:
    try:
        if isinstance(value, bool) or not isinstance(value, int | float):
            return frame.filter(pl.col(column) == value)
        return frame.filter(pl.col(column).cast(pl.Float64, strict=False) == float(value))
    except (pl.exceptions.PolarsError, TypeError, ValueError):
        return frame.head(0)


def _row_label(frame: pl.DataFrame, row: dict[str, Any]) -> str | None:
    for column in frame.columns:
        cell = row.get(column)
        if column != ROW_COLUMN and isinstance(cell, str) and cell.strip():
            return cell
    return None


def future_row(
    workbooks: list[LoadedWorkbook], sql: str, value: Any, today: date
) -> FutureRow | None:
    """The row a 1×1 SQL result was read from, when that row is dated after `today`.

    A table qualifies when it has a Date/Datetime column; the value is looked up in the
    non-date columns the SQL names; a match counts only if *every* row holding that value
    is dated after `today` (a value that also exists in a past row cannot be attributed —
    the guard stays silent rather than guess). `None` when nothing qualifies."""
    if value is None or isinstance(value, datetime | date):
        return None
    tables = {name: frame for wb in workbooks for name, frame in wb.tables.items()}
    try:
        guarded = guard_select(sql, set(tables))
    except SqlRejectedError:
        return None
    for name in guarded.tables:
        frame = tables[name]
        date_column = _date_column(frame)
        if date_column is None:
            continue
        value_columns = [
            c
            for c in frame.columns
            if c not in (ROW_COLUMN, date_column)
            and not isinstance(frame.schema[c], _DATE_TYPES)
            and _named_in(sql, c)
        ]
        for column in value_columns:
            matched = _matching_rows(frame, column, value)
            if matched.height == 0:
                continue
            dates = [_to_date(d) for d in matched[date_column].to_list()]
            if any(d is None or d <= today for d in dates):
                return None
            first = matched.sort(date_column).head(1).to_dicts()[0]
            return FutureRow(
                table=name,
                date_column=date_column,
                excel_row=int(first[ROW_COLUMN]),
                label=_row_label(frame, first),
            )
    return None
