"""SPEC_04 §4 whitelist: everything not provably a read-only SELECT over known tables is
rejected before DuckDB ever sees it."""

from __future__ import annotations

import pytest

from app.excel.sql_guard import GuardedSql, SqlRejectedError, guard_select

TABLES = {"covenant_report__summary", "monthly_production_2026__production"}

MALICIOUS = [
    "DROP TABLE covenant_report__summary",
    "SELECT 1; DROP TABLE covenant_report__summary",
    "SELECT * FROM covenant_report__summary; --",
    "SELECT * FROM covenant_report__summary -- comment",
    "SELECT * FROM covenant_report__summary /* ; */",
    "SELECT * FROM read_csv('/etc/passwd')",
    "SELECT * FROM read_csv_auto('/data/x.csv')",
    "ATTACH '/data/x.db' AS x",
    "INSTALL httpfs",
    "LOAD httpfs",
    "PRAGMA database_list",
    "COPY covenant_report__summary TO '/tmp/x.csv'",
    "SELECT * FROM duckdb_settings()",
    "SELECT current_setting('home_directory')",
    "WITH x AS (SELECT 1) INSERT INTO covenant_report__summary SELECT * FROM x",
    "SELECT * FROM unknown_table",
    "select * from covenant_report__summary union all select * from duckdb_databases()",
    "SELECT * INTO t2 FROM covenant_report__summary",
    "SET threads = 64",
    "UPDATE covenant_report__summary SET dscr = 9",
    "  sElEcT * FROM read_parquet('x')",
    "",
    "EXPLAIN SELECT * FROM covenant_report__summary",
    "SELECT * FROM glob('/data/*')",
]


@pytest.mark.parametrize("sql", MALICIOUS)
def test_malicious_or_unknown_sql_is_rejected(sql: str) -> None:
    with pytest.raises(SqlRejectedError):
        guard_select(sql, TABLES)


def test_plain_select_gets_a_limit() -> None:
    guarded = guard_select("SELECT period, dscr FROM covenant_report__summary", TABLES)
    assert guarded == GuardedSql(
        sql="SELECT period, dscr FROM covenant_report__summary LIMIT 200",
        tables=("covenant_report__summary",),
    )


def test_oversized_limit_is_capped_and_small_limit_kept() -> None:
    assert guard_select("SELECT * FROM covenant_report__summary LIMIT 100000", TABLES).sql.endswith(
        "LIMIT 200"
    )
    assert guard_select("SELECT * FROM covenant_report__summary LIMIT 5", TABLES).sql.endswith(
        "LIMIT 5"
    )


def test_cte_and_join_over_known_tables_are_allowed() -> None:
    sql = (
        "WITH p AS (SELECT month, mwh FROM monthly_production_2026__production) "
        "SELECT p.month, s.dscr FROM p JOIN covenant_report__summary s ON 1=1 "
        "WHERE s.period = 'Q2_2026'"
    )
    guarded = guard_select(sql, TABLES)
    assert set(guarded.tables) == TABLES


def test_string_literals_do_not_trigger_keyword_rules() -> None:
    guarded = guard_select("SELECT * FROM covenant_report__summary WHERE note = 'drop it'", TABLES)
    assert guarded.tables == ("covenant_report__summary",)
