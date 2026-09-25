"""Read-only SELECT whitelist for LLM-written SQL (SPEC_04 §4, ADR-011).

Pure function, no DuckDB: the guard is the first line of defence, DuckDB's
`enable_external_access=false` (engine.py) the second. Everything the guard cannot prove
safe is rejected — a rejected query costs a Turkish message, an accepted bad query could
cost data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

DEFAULT_ROW_LIMIT = 200

FORBIDDEN_KEYWORDS = frozenset(
    {
        "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE", "ATTACH",
        "DETACH", "INSTALL", "LOAD", "PRAGMA", "COPY", "EXPORT", "IMPORT", "CALL", "SET",
        "RESET", "EXECUTE", "PREPARE", "VACUUM", "CHECKPOINT", "BEGIN", "COMMIT",
        "ROLLBACK", "GRANT", "REVOKE", "INTO", "FORCE",
    }
)  # fmt: skip
FORBIDDEN_FUNCTIONS = frozenset(
    {
        "read_csv", "read_csv_auto", "read_parquet", "read_json", "read_json_auto",
        "read_text", "read_blob", "glob", "sniff_csv", "parquet_scan", "csv_scan",
        "json_scan", "httpfs", "current_setting", "getenv", "read_ndjson",
    }
)  # fmt: skip

_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_STRING = re.compile(r"'(?:[^']|'')*'")
_LIMIT = re.compile(r"\bLIMIT\s+(\d+)\s*$", re.IGNORECASE)
_FROM_JOIN = re.compile(r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)


class SqlRejectedError(ValueError):
    """The query broke a whitelist rule; `reason` is log-only (English)."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class GuardedSql:
    sql: str
    tables: tuple[str, ...]


def guard_select(
    sql: str, known_tables: set[str], *, row_limit: int = DEFAULT_ROW_LIMIT
) -> GuardedSql:
    text = sql.strip()
    if not text:
        raise SqlRejectedError("empty")
    if ";" in text:
        raise SqlRejectedError("semicolon")
    if "--" in text or "/*" in text or "*/" in text:
        raise SqlRejectedError("comment")
    head = text.lstrip("(").split(None, 1)[0].upper() if text else ""
    if head not in {"SELECT", "WITH"}:
        raise SqlRejectedError(f"must start with SELECT, got {head!r}")

    without_strings = _STRING.sub("''", text)
    tokens = [t.upper() for t in _TOKEN.findall(without_strings)]
    for token in tokens:
        if token in FORBIDDEN_KEYWORDS:
            raise SqlRejectedError(f"forbidden keyword {token}")
        lowered = token.lower()
        if (
            lowered in FORBIDDEN_FUNCTIONS
            or lowered.startswith("duckdb_")
            or lowered.startswith("sqlite_")
        ):
            raise SqlRejectedError(f"forbidden function/table {token}")

    ctes = {
        m.lower()
        for m in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s+AS\s*\(", without_strings, re.IGNORECASE)
    }
    referenced = [m for m in _FROM_JOIN.findall(without_strings)]
    tables: list[str] = []
    for name in referenced:
        lowered = name.lower()
        if lowered in ctes:
            continue
        if lowered not in {t.lower() for t in known_tables}:
            raise SqlRejectedError(f"unknown table {name}")
        if lowered not in tables:
            tables.append(lowered)
    if not tables:
        raise SqlRejectedError("no known table referenced")

    match = _LIMIT.search(text)
    if match is None:
        text = f"{text} LIMIT {row_limit}"
    elif int(match.group(1)) > row_limit:
        text = _LIMIT.sub(f"LIMIT {row_limit}", text)
    return GuardedSql(sql=text, tables=tuple(tables))
