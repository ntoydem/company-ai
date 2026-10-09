"""ADR-030 F-8 on the Excel path: SQL results reach the model already formatted."""

from __future__ import annotations

from datetime import datetime

from app.excel.calc import QueryResult, SourceRange
from app.services.excel_ask import _sql_value, format_value


def _result(columns: tuple[str, ...], rows: tuple[tuple[object, ...], ...]) -> QueryResult:
    return QueryResult(
        columns=columns,
        rows=rows,
        sources=(SourceRange("f.xlsx", "Inputs", "A1:B3"),),
        truncated=False,
    )


def test_single_cell_takes_its_unit_from_the_column_label_under_the_flag() -> None:
    value, unit, table = _sql_value(_result(("Debt (EUR)",), ((1000000.0,),)), ek_f=True)
    assert (value, unit, table) == (1000000.0, "EUR", "")
    assert format_value(value, unit, ek_f=True) == "1.000.000 EUR"
    value, unit, table = _sql_value(
        _result(("Financial close",), ((datetime(2021, 11, 15),),)), ek_f=True
    )
    assert (value, unit, table) == ("15.11.2021", "", "")


def test_flag_off_is_the_phase_4_formatter_byte_for_byte() -> None:
    assert _sql_value(_result(("Debt (EUR)",), ((1000000.0,),))) == (1000000.0, "", "")
    _, _, table = _sql_value(
        _result(("Capex (EUR)", "Financial close"), ((72000000.0, datetime(2021, 11, 15)),))
    )
    assert table == "Capex (EUR) | Financial close\n72000000.0 | 2021-11-15 00:00:00"
    assert format_value(-894000, "TRY") == "-894.000 TRY"
    assert format_value(38.2, "%") == "%38,2"
    assert format_value(1234.5678, "EUR") == "1.234,57 EUR"  # the old rounding, flag off only
    assert format_value(1234.5678, "EUR", ek_f=True) == "1.234,5678 EUR"  # no rounding


def test_table_cells_are_formatted_by_code_before_the_model_sees_them() -> None:
    value, unit, table = _sql_value(
        _result(
            ("Item", "Capex (EUR)", "Financial close", "DSCR"),
            (("Ankara", 72000000.0, datetime(2021, 11, 15, 0, 0), 1.37),),
        ),
        ek_f=True,
    )
    assert value is None and unit == ""
    assert table.splitlines() == [
        "Item | Capex (EUR) | Financial close | DSCR",
        "Ankara | 72.000.000 EUR | 15.11.2021 | 1,37x",
    ]
    assert "72000000" not in table and "00:00:00" not in table
