"""`POST /api/excel/ask`, `GET /api/excel/{id}/inspect` and the Excel-family upload path
(Phase 4.2). The planning/answering LLM is `FakeLLMClient`; the engine is the real
`CachedValueEngine` over the committed demo workbooks."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.repositories import user_repo
from app.services.excel_ask import NO_DATA_TEXT, SQL_REJECTED_TEXT
from app.services.security import hash_password
from tests.department_fixtures import add_user_to_department, make_department
from tests.fakes import FakeLLMClient

EXCEL_DIR = Path(__file__).resolve().parent.parent / "seed_data" / "excel"
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _upload_workbook(
    client: TestClient, file: str = "Covenant_Report.xlsx", *, department: str | None = None
) -> dict[str, object]:
    data = {
        "title": file,
        "document_type": "Covenant Report",
        "document_date": "2026-08-15",
        "counterparty": "PQR Bank",
    }
    if department:
        data["department"] = department
    response = client.post(
        "/api/documents/upload",
        files={"file": (file, (EXCEL_DIR / file).read_bytes(), XLSX_TYPE)},
        data=data,
    )
    assert response.status_code == 201, response.text
    body: dict[str, object] = response.json()
    return body


def _plan(kind: str, **fields: object) -> str:
    return json.dumps({"kind": kind, **fields})


# ---------------------------------------------------------------- upload / inspect


def test_xlsx_upload_is_ready_without_an_ocr_job(client: TestClient, admin_user: User) -> None:
    body = _upload_workbook(client)
    assert body["ingestion_status"] == "ready"
    detail = client.get(f"/api/documents/{body['id']}").json()
    assert detail["page_count"] == 13  # Summary + 11 quarter sheets + hidden _meta
    assert detail["has_macros"] is False


def test_inspect_lists_sheets_named_ranges_and_hidden_meta(
    client: TestClient, admin_user: User
) -> None:
    body = _upload_workbook(client, "Financial_Model_2026.xlsx")
    response = client.get(f"/api/excel/{body['id']}/inspect")
    assert response.status_code == 200, response.text
    info = response.json()
    names = {s["name"]: s for s in info["sheets"]}
    assert set(names) == {"Inputs", "Debt", "DSCR", "Cashflow", "_meta"}
    assert names["_meta"]["hidden"] is True
    assert "Outstanding_DemoToday" in {n["name"] for n in info["named_ranges"]}
    assert info["needs_recalculation"] is False and info["has_macros"] is False
    assert "financial_model_2026__debt" in info["tables"]


def test_inspect_of_a_pdf_is_422_and_unknown_is_404(client: TestClient, admin_user: User) -> None:
    from tests.test_documents import _upload

    pdf = _upload(client).json()
    assert client.get(f"/api/excel/{pdf['id']}/inspect").status_code == 422
    assert client.get("/api/excel/00000000-0000-0000-0000-000000000000/inspect").status_code == 404


def test_xlsm_is_flagged_never_executed(
    client: TestClient, admin_user: User, tmp_path: Path
) -> None:
    """SPEC_04 §1: a VBA project is detected from the zip and flagged; nothing loads it."""
    source = EXCEL_DIR / "Budget_vs_Actual_2026.xlsx"
    target = io.BytesIO()
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(target, "w") as dst:
        for item in src.infolist():
            dst.writestr(item, src.read(item.filename))
        dst.writestr(
            "xl/vbaProject.bin", b'\x00fake vba project: Sub Auto_Open() Kill "*.*" End Sub'
        )
    response = client.post(
        "/api/documents/upload",
        files={
            "file": (
                "budget.xlsm",
                target.getvalue(),
                "application/vnd.ms-excel.sheet.macroEnabled.12",
            )
        },
        data={
            "title": "macro",
            "document_type": "Budget",
            "document_date": "2026-07-31",
            "counterparty": "x",
        },
    )
    assert response.status_code == 201, response.text
    document_id = response.json()["id"]
    detail = client.get(f"/api/documents/{document_id}").json()
    assert detail["has_macros"] is True
    info = client.get(f"/api/excel/{document_id}/inspect").json()
    assert info["kind"] == "xlsm" and info["has_macros"] is True
    assert "Variance_Q2_2026" in {n["name"] for n in info["named_ranges"]}


def test_csv_upload_is_accepted_and_binary_junk_is_not(
    client: TestClient, admin_user: User
) -> None:
    csv_bytes = b"period;amount\nQ1_2026;100\n"
    response = client.post(
        "/api/documents/upload",
        files={"file": ("opex.csv", csv_bytes, "text/csv")},
        data={
            "title": "opex",
            "document_type": "csv",
            "document_date": "2026-07-31",
            "counterparty": "x",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["ingestion_status"] == "ready"
    junk = client.post(
        "/api/documents/upload",
        files={"file": ("x.csv", b"\x00\xff\xfe binary", "text/csv")},
        data={
            "title": "j",
            "document_type": "csv",
            "document_date": "2026-07-31",
            "counterparty": "x",
        },
    )
    assert junk.status_code == 415


# ---------------------------------------------------------------- ask


def test_ask_dscr_uses_the_predefined_function_and_cites_the_cell(
    client: TestClient, admin_user: User, fake_llm: FakeLLMClient, db_session: Session
) -> None:
    """PHASES.md 4.2 kabul kriteri: "Ankara RES 2026 Q2 DSCR kaç?" -> DuckDB/predefined +
    `Covenant_Report.xlsx Q2_2026!D14`; audit row carries the Excel sources."""
    _upload_workbook(client)
    fake_llm.replies = [
        _plan("function", name="dscr", params={"period": "Q2_2026"}),
        "Ankara RES'in 2026 Q2 DSCR değeri 1,37x olarak hesaplanmıştır.",
    ]
    response = client.post("/api/excel/ask", json={"question": "Ankara RES 2026 Q2 DSCR kaç?"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["answered"] is True
    assert body["value"] == 1.37 and body["formatted_value"] == "1,37x"
    assert body["sources"][0]["label"] == "Covenant_Report.xlsx Q2_2026!D14"
    assert body["plan_kind"] == "function"
    assert body["excel_files"] == ["Covenant_Report.xlsx"]
    assert "1,37x" in body["answer"]
    # Planning prompt saw the catalogue (tables + functions), never a number to compute.
    plan_request = fake_llm.requests[0]
    assert "covenant_report__summary" in plan_request.user and "dscr(period)" in plan_request.user
    assert plan_request.response_format == "json_object"

    row = db_session.scalar(select(AuditLog).order_by(AuditLog.timestamp.desc()))
    assert row is not None
    assert row.query_type == "DATA_QUERY"
    assert row.excel_files_used == ["Covenant_Report.xlsx"]
    assert row.sources[0]["label"] == "Covenant_Report.xlsx Q2_2026!D14"


def test_ask_sql_path_sums_production_and_cites_the_range(
    client: TestClient, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    _upload_workbook(client, "Monthly_Production_2026.xlsx")
    fake_llm.replies = [
        _plan(
            "sql",
            sql=(
                "SELECT SUM(mwh) FROM monthly_production_2026__production WHERE month LIKE '2026-%'"
            ),
        ),
        "2026 yılında toplam üretim 108.858 MWh.",
    ]
    body = client.post("/api/excel/ask", json={"question": "2026'da toplam üretim kaç MWh?"}).json()
    assert body["answered"] is True and body["plan_kind"] == "sql"
    assert body["value"] == 108858
    assert body["sources"][0]["file"] == "Monthly_Production_2026.xlsx"
    assert body["sources"][0]["sheet"] == "Production"


def test_ask_rejects_dangerous_sql_from_the_model(
    client: TestClient, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    _upload_workbook(client)
    fake_llm.replies = [_plan("sql", sql="SELECT 1; DROP TABLE covenant_report__summary")]
    response = client.post("/api/excel/ask", json={"question": "Tabloyu sil?"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["answered"] is False and body["answer"] == SQL_REJECTED_TEXT
    assert len(fake_llm.requests) == 1  # no answering call for a rejected plan


def test_ask_falls_back_to_the_template_when_the_model_alters_the_number(
    client: TestClient, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    """ADR-011: the final figure never comes from the model."""
    _upload_workbook(client)
    fake_llm.replies = [
        _plan("function", name="dscr", params={"period": "Q2_2026"}),
        "DSCR yaklaşık 1,4x civarındadır.",  # rounded by the model -> discarded
    ]
    body = client.post("/api/excel/ask", json={"question": "2026 Q2 DSCR?"}).json()
    assert body["answered"] is True
    assert body["answer"].startswith("Sonuç: 1,37x")


def test_ask_without_any_visible_workbook_says_no_data(
    client: TestClient, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    body = client.post("/api/excel/ask", json={"question": "DSCR?"}).json()
    assert body["answered"] is False and body["answer"] == NO_DATA_TEXT
    assert fake_llm.requests == []


def test_employee_cannot_query_another_departments_workbook(
    client: TestClient, admin_user: User, fake_llm: FakeLLMClient, db_session: Session
) -> None:
    """ADR-004: the Excel path starts from `allowed_document_ids` like everything else."""
    make_department(db_session, slug="finans")
    enerji = make_department(db_session, slug="enerji_grubu")
    _upload_workbook(client, department="finans")  # uploaded by admin into finans
    employee = user_repo.create(
        db_session,
        username="enerji_test",
        password_hash=hash_password("x"),
        display_name="Enerji",
        role=UserRole.employee,
    )
    add_user_to_department(db_session, employee, enerji)
    from app.api.deps import get_current_user
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: employee
    try:
        body = client.post("/api/excel/ask", json={"question": "DSCR?"}).json()
    finally:
        app.dependency_overrides[get_current_user] = lambda: admin_user
    assert body["answered"] is False and body["answer"] == NO_DATA_TEXT
    assert fake_llm.requests == []
