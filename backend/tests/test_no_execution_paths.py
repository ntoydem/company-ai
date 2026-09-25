"""SPEC_04 §1/§4 static guarantee: the Excel path has no way to run a macro, a shell or
model-written Python. If someone adds one, this test names the file."""

from __future__ import annotations

import re
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "app"
EXCEL_SOURCES = [
    *(APP / "excel").glob("*.py"),
    APP / "services" / "excel_ask.py",
    APP / "api" / "excel.py",
]
FORBIDDEN = re.compile(
    r"\b(subprocess|os\.system|os\.popen|soffice|libreoffice|keep_vba\s*=\s*True|\bexec\(|\beval\(|importlib|xlwings|win32com)\b"
)


def test_excel_code_has_no_execution_path() -> None:
    assert EXCEL_SOURCES, "excel sources not found"
    offenders = []
    for path in EXCEL_SOURCES:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if FORBIDDEN.search(line):
                offenders.append(f"{path.name}:{number}: {line.strip()}")
    assert offenders == [], "\n".join(offenders)


def test_duckdb_is_opened_without_external_access() -> None:
    source = (APP / "excel" / "calc.py").read_text(encoding="utf-8")
    assert '"enable_external_access": False' in source
