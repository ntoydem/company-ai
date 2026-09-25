"""`CachedValueEngine` + predefined functions over the four committed demo workbooks
(`seed_data/excel/`, recalculated by LibreOffice, validated by `validate_excel.py`)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.excel.calc import (
    CachedValueEngine,
    LoadedWorkbook,
    NeedsRecalculationError,
    QueryTimeoutError,
    table_name,
)
from app.excel.functions import FunctionError, run_function
from app.excel.inspect import inspect_file
from app.excel.sql_guard import SqlRejectedError

EXCEL_DIR = Path(__file__).resolve().parent.parent / "seed_data" / "excel"
FILES = (
    "Financial_Model_2026.xlsx",
    "Covenant_Report.xlsx",
    "Budget_vs_Actual_2026.xlsx",
    "Monthly_Production_2026.xlsx",
)


@pytest.fixture(scope="module")
def engine() -> CachedValueEngine:
    return CachedValueEngine(timeout_s=10, row_limit=200)


@pytest.fixture(scope="module")
def workbooks(engine: CachedValueEngine) -> list[LoadedWorkbook]:
    return [engine.load(EXCEL_DIR / f) for f in FILES]


def test_generated_workbooks_have_no_uncached_formula_and_a_hidden_meta_sheet() -> None:
    """PHASES.md 4.2 kabul kriteri 1: cached değerler dolu (`data_only` boş hücre yok)."""
    for file in FILES:
        info = inspect_file(EXCEL_DIR / file)
        assert info.formula_cells > 0, file
        assert info.formula_cells_without_cache == 0, file
        assert any(s.name == "_meta" and s.hidden for s in info.sheets), file
        assert not info.has_macros


def test_dscr_q2_2026_comes_from_the_covenant_report_cell(
    workbooks: list[LoadedWorkbook], engine: CachedValueEngine
) -> None:
    """PHASES.md 4.2 kabul kriteri 2: "Ankara RES 2026 Q2 DSCR kaç?" ->
    Covenant_Report.xlsx Q2_2026!D14."""
    result = run_function(engine, workbooks, "dscr", {"period": "2026 Q2"})
    assert result.value == pytest.approx(1.37)
    assert result.source.label == "Covenant_Report.xlsx Q2_2026!D14"


def test_outstanding_debt_today_and_after_a_quarter(
    workbooks: list[LoadedWorkbook], engine: CachedValueEngine
) -> None:
    today = run_function(engine, workbooks, "outstanding_debt", {"as_of": "today"})
    assert today.value == pytest.approx(44_100_000)
    assert today.source.file == "Financial_Model_2026.xlsx" and today.source.sheet == "Debt"
    q = run_function(engine, workbooks, "outstanding_debt", {"as_of": "Q4_2024"})
    assert q.value == pytest.approx(48_300_000)
    assert q.source.label == "Covenant_Report.xlsx Q4_2024!D12"


def test_budget_variance_production_and_capacity_factor(
    workbooks: list[LoadedWorkbook], engine: CachedValueEngine
) -> None:
    variance = run_function(engine, workbooks, "budget_variance", {"period": "Q2 2026"})
    assert variance.value == pytest.approx(882_000)
    assert variance.unit == "TRY" and variance.source.sheet == "Summary"

    month = run_function(engine, workbooks, "production", {"period": "2026-08"})
    assert month.value == pytest.approx(13_538)
    year = run_function(engine, workbooks, "production", {"period": "2025"})
    assert year.value == pytest.approx(164_244)
    assert year.source.label == "Monthly_Production_2026.xlsx KPI!B4"
    quarter = run_function(engine, workbooks, "production", {"period": "Q2_2026"})
    assert quarter.value == pytest.approx(12_561 + 12_304 + 10_951)
    assert quarter.source.sheet == "Production" and quarter.source.ref.startswith("A")

    cf = run_function(engine, workbooks, "capacity_factor", {"period": "2026-01"})
    assert cf.value == pytest.approx(38.2)


def test_function_errors_on_bad_period_or_unknown_name(
    workbooks: list[LoadedWorkbook], engine: CachedValueEngine
) -> None:
    with pytest.raises(FunctionError):
        run_function(engine, workbooks, "dscr", {"period": "some day"})
    with pytest.raises(FunctionError):
        run_function(engine, workbooks, "nope", {})


def test_sql_sum_over_the_production_table_cites_the_sheet_range(
    workbooks: list[LoadedWorkbook], engine: CachedValueEngine
) -> None:
    table = table_name("Monthly_Production_2026.xlsx", "Production")
    result = engine.run_sql(
        workbooks, f"SELECT SUM(mwh) AS total FROM {table} WHERE month LIKE '2026-%'"
    )
    assert result.columns == ("total",)
    assert result.rows[0][0] == pytest.approx(108_858)
    assert len(result.sources) == 1
    assert result.sources[0].file == "Monthly_Production_2026.xlsx"
    assert result.sources[0].sheet == "Production"
    assert result.sources[0].ref.startswith("A2:")


def test_sql_row_column_narrows_the_cited_range(
    workbooks: list[LoadedWorkbook], engine: CachedValueEngine
) -> None:
    table = table_name("Covenant_Report.xlsx", "Summary")
    result = engine.run_sql(
        workbooks, f"SELECT _row, quarter, dscr FROM {table} WHERE quarter = 'Q2_2026'"
    )
    assert result.rows[0][1:] == ("Q2_2026", pytest.approx(1.37))
    assert result.sources[0].ref == "A12:E12"


def test_sql_guard_and_external_access_are_both_enforced(
    workbooks: list[LoadedWorkbook], engine: CachedValueEngine
) -> None:
    with pytest.raises(SqlRejectedError):
        engine.run_sql(workbooks, "SELECT * FROM read_csv('/etc/passwd')")
    with pytest.raises(SqlRejectedError):
        engine.run_sql(workbooks, "DROP TABLE covenant_report__summary")


def test_sql_timeout_interrupts_a_runaway_query(workbooks: list[LoadedWorkbook]) -> None:
    fast = CachedValueEngine(timeout_s=0.2, row_limit=10)
    table = table_name("Monthly_Production_2026.xlsx", "Production")
    with pytest.raises(QueryTimeoutError):
        fast.run_sql(
            workbooks,
            f"SELECT COUNT(*) FROM {table} a, {table} b, {table} c, {table} d, "
            f"{table} e, {table} f",
        )


def test_workbook_without_cached_values_is_refused(
    tmp_path: Path, engine: CachedValueEngine
) -> None:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws["A1"], ws["A2"], ws["A3"] = "x", 1, "=A2*2"
    path = tmp_path / "raw.xlsx"
    wb.save(path)
    with pytest.raises(NeedsRecalculationError):
        engine.load(path)


def test_csv_is_loaded_as_a_single_table(tmp_path: Path, engine: CachedValueEngine) -> None:
    path = tmp_path / "opex.csv"
    path.write_text("period;amount\nQ1_2026;100\nQ2_2026;250\n", encoding="utf-8")
    loaded = engine.load(path)
    assert list(loaded.tables) == ["opex__opex"]
    result = engine.run_sql([loaded], "SELECT SUM(CAST(amount AS DOUBLE)) FROM opex__opex")
    assert result.rows[0][0] == pytest.approx(350)
    assert loaded.info.kind == "csv" and not loaded.info.has_macros
