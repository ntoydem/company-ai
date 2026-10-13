"""`POST /api/excel/ask`, `GET /api/excel/{id}/inspect` and the Excel-family upload path
(Phase 4.2). The planning/answering LLM is `FakeLLMClient`; the engine is the real
`CachedValueEngine` over the committed demo workbooks."""

from __future__ import annotations

import io
import json
import uuid
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_calculation_engine
from app.core.config import Settings
from app.models.audit_log import AuditLog
from app.models.document import Document, DocumentReviewStatus
from app.models.user import User, UserRole
from app.repositories import user_repo
from app.schemas.excel import ExcelAskRequest, ExcelAskResponse
from app.services.answer_prompt import NO_ANSWER_TEXT
from app.services.excel_ask import (
    ANSWER_SYSTEM_PROMPT,
    NO_DATA_TEXT,
    PLAN_SYSTEM_PROMPT,
    SQL_REJECTED_TEXT,
    answer_data_question,
)
from app.services.llm import LLMRequest
from app.services.security import hash_password
from tests.department_fixtures import (
    add_user_to_department,
    make_department,
    make_department_manager,
)
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


def _publish(session: Session, body: dict[str, object]) -> dict[str, object]:
    """B-28: an admin upload waits for the department's review; these tests exercise the
    Excel engine, not the approval flow, so the workbook is published directly."""
    document = session.get(Document, uuid.UUID(str(body["id"])))
    assert document is not None
    document.review_status = DocumentReviewStatus.approved
    session.commit()
    return body


def _plan(kind: str, **fields: object) -> str:
    return json.dumps({"kind": kind, **fields})


# ---------------------------------------------------------------- upload / inspect


def test_xlsx_upload_is_ready_without_an_ocr_job(client: TestClient, admin_user: User) -> None:
    body = _upload_workbook(client)
    assert body["ingestion_status"] == "ready" and body["file_kind"] == "xlsx"
    detail = client.get(f"/api/documents/{body['id']}").json()
    assert detail["page_count"] == 13  # Summary + 11 quarter sheets + hidden _meta
    assert detail["has_macros"] is False and detail["file_kind"] == "xlsx"


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
    _publish(db_session, _upload_workbook(client))
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
    client: TestClient, admin_user: User, fake_llm: FakeLLMClient, db_session: Session
) -> None:
    _publish(db_session, _upload_workbook(client, "Monthly_Production_2026.xlsx"))
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
    client: TestClient, admin_user: User, fake_llm: FakeLLMClient, db_session: Session
) -> None:
    _publish(db_session, _upload_workbook(client))
    fake_llm.replies = [_plan("sql", sql="SELECT 1; DROP TABLE covenant_report__summary")]
    response = client.post("/api/excel/ask", json={"question": "Tabloyu sil?"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["answered"] is False and body["answer"] == SQL_REJECTED_TEXT
    assert len(fake_llm.requests) == 1  # no answering call for a rejected plan


def test_ask_falls_back_to_the_template_when_the_model_alters_the_number(
    client: TestClient, admin_user: User, fake_llm: FakeLLMClient, db_session: Session
) -> None:
    """ADR-011: the final figure never comes from the model."""
    _publish(db_session, _upload_workbook(client))
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
    finans = make_department(db_session, slug="finans")
    make_department_manager(db_session, finans)
    enerji = make_department(db_session, slug="enerji_grubu")
    _publish(db_session, _upload_workbook(client, department="finans"))  # admin → finans
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


# ---------------------------------------------------------------- S0-a: engine guard + one retry


TABLE_SQL = "SELECT month, mwh FROM monthly_production_2026__production WHERE month LIKE '2026-%'"
SCALAR_SQL = "SELECT SUM(mwh) FROM monthly_production_2026__production WHERE month LIKE '2026-%'"


def _no_workbook_figures(requests: list[LLMRequest]) -> None:
    """Rule 3 / ADR-011: no cell value of the Production sheet reaches a *planning* call —
    neither a monthly MWh figure nor the yearly sum (the phrasing call gets the engine's
    one value, nothing else)."""
    for request in requests:
        assert request.system == PLAN_SYSTEM_PROMPT
        assert "14344" not in request.user and "108858" not in request.user
        assert "108.858" not in request.user


def test_scalar_sql_result_keeps_the_old_two_call_flow(
    client: TestClient, admin_user: User, fake_llm: FakeLLMClient, db_session: Session
) -> None:
    """(1) 1×1 → plan + phrasing, exactly as before; no feedback text anywhere."""
    _publish(db_session, _upload_workbook(client, "Monthly_Production_2026.xlsx"))
    fake_llm.replies = [_plan("sql", sql=SCALAR_SQL), "2026 yılında toplam üretim 108.858 MWh."]
    body = client.post("/api/excel/ask", json={"question": "2026'da toplam üretim kaç MWh?"}).json()
    assert body["answered"] is True and body["value"] == 108858
    assert len(fake_llm.requests) == 2
    assert fake_llm.requests[1].system == ANSWER_SYSTEM_PROMPT
    assert "GERİ BİLDİRİM" not in fake_llm.requests[0].user


def test_table_result_triggers_one_replan_with_feedback_and_no_table_to_the_model(
    client: TestClient, admin_user: User, fake_llm: FakeLLMClient, db_session: Session
) -> None:
    """(2) N×M → a second planning call whose user prompt carries the feedback (row × column
    count, the column names, the previous SQL, candidate row labels — no figures); the
    second plan's 1×1 result is then phrased as usual."""
    _publish(db_session, _upload_workbook(client, "Monthly_Production_2026.xlsx"))
    fake_llm.replies = [
        _plan("sql", sql=TABLE_SQL),
        _plan("sql", sql=SCALAR_SQL),
        "2026 yılında toplam üretim 108.858 MWh.",
    ]
    body = client.post("/api/excel/ask", json={"question": "2026'da toplam üretim kaç MWh?"}).json()
    assert body["answered"] is True and body["value"] == 108858 and body["plan_kind"] == "sql"
    assert body["plan"]["sql"] == SCALAR_SQL  # the plan that produced the answer
    assert [r.system for r in fake_llm.requests] == [
        PLAN_SYSTEM_PROMPT,
        PLAN_SYSTEM_PROMPT,
        ANSWER_SYSTEM_PROMPT,
    ]
    retry = fake_llm.requests[1].user
    assert "satır × 2 sütun döndürdü; tek değer gerekiyor; sütunlar: ['month', 'mwh']" in retry
    assert TABLE_SQL in retry and "Aday satır başlıkları: ['2026-01'" in retry
    assert retry.startswith(fake_llm.requests[0].user)  # catalogue + question unchanged
    _no_workbook_figures(fake_llm.requests[:2])
    phrasing = fake_llm.requests[2].user
    assert "SONUÇ: 108.858\n" in phrasing and "14344" not in phrasing  # the engine's value only


def test_second_table_result_ends_in_the_fixed_sentence_without_any_figure(
    client: TestClient, admin_user: User, fake_llm: FakeLLMClient, db_session: Session
) -> None:
    """(3) both attempts N×M → answered=false, the canonical no-answer sentence, no number
    in the answer, no phrasing call, the tried sheet/range listed as sources."""
    _publish(db_session, _upload_workbook(client, "Monthly_Production_2026.xlsx"))
    fake_llm.replies = [_plan("sql", sql=TABLE_SQL), _plan("sql", sql=TABLE_SQL)]
    body = client.post("/api/excel/ask", json={"question": "Aylık üretim ne kadar?"}).json()
    assert body["answered"] is False and body["answer"] == NO_ANSWER_TEXT
    assert body["value"] is None and body["formatted_value"] is None
    assert not any(ch.isdigit() for ch in body["answer"])
    assert len(fake_llm.requests) == 2  # two plans, no phrasing call
    assert all(r.system == PLAN_SYSTEM_PROMPT for r in fake_llm.requests)
    _no_workbook_figures(fake_llm.requests)
    assert body["sources"] and body["sources"][0]["sheet"] == "Production"
    assert body["excel_files"] == ["Monthly_Production_2026.xlsx"]
    row = db_session.scalar(select(AuditLog).order_by(AuditLog.timestamp.desc()))
    assert row is not None and row.error is None
    assert row.sources[0]["kind"] == "excel" and row.answer == NO_ANSWER_TEXT


def test_ambiguous_hook_carries_candidate_labels_but_no_values(
    admin_user: User, db_session: Session, settings: Settings, client: TestClient
) -> None:
    """The B2 hook: `ExcelAskResult.ambiguous` lists the row labels the user could pick
    from; nothing numeric. Not on the wire in this round."""
    _publish(db_session, _upload_workbook(client, "Monthly_Production_2026.xlsx"))
    fake = FakeLLMClient(replies=[_plan("sql", sql=TABLE_SQL), _plan("sql", sql=TABLE_SQL)])
    result = answer_data_question(
        db_session,
        admin_user,
        ExcelAskRequest(question="Aylık üretim?"),
        fake,
        settings,
        get_calculation_engine(),
        write_audit=False,
    )
    assert result.ambiguous is not None and result.answered is False
    assert result.ambiguous.attempts == 2 and result.ambiguous.columns == ("month", "mwh")
    assert result.ambiguous.rows > 1 and "2026-01" in result.ambiguous.candidates
    assert all(not _looks_numeric(c) for c in result.ambiguous.candidates)
    assert "ambiguous" not in ExcelAskResponse.model_fields


def _looks_numeric(text: str) -> bool:
    try:
        float(text)
    except ValueError:
        return False
    return True


def test_plan_call_uses_llm_model_excel_plan_only_when_set(
    admin_user: User, db_session: Session, settings: Settings, client: TestClient
) -> None:
    """(4) empty → classify model (today); set → that model — for the planning call only,
    the phrasing call keeps `LLM_MODEL_ANSWER`."""
    _publish(db_session, _upload_workbook(client))
    plan = _plan("function", name="dscr", params={"period": "Q2_2026"})

    fake = FakeLLMClient(replies=[plan, "DSCR 1,37x."])
    answer_data_question(
        db_session,
        admin_user,
        ExcelAskRequest(question="2026 Q2 DSCR?"),
        fake,
        settings.model_copy(update={"llm_model_excel_plan": ""}),
        get_calculation_engine(),
        write_audit=False,
    )
    assert [r.model for r in fake.requests] == [
        settings.llm_model_classify,
        settings.llm_model_answer,
    ]

    fake = FakeLLMClient(replies=[plan, "DSCR 1,37x."])
    answer_data_question(
        db_session,
        admin_user,
        ExcelAskRequest(question="2026 Q2 DSCR?"),
        fake,
        settings.model_copy(update={"llm_model_excel_plan": "plan-model-x"}),
        get_calculation_engine(),
        write_audit=False,
    )
    assert [r.model for r in fake.requests] == ["plan-model-x", settings.llm_model_answer]


def test_llm_model_excel_plan_env_is_read_and_defaults_to_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert Settings().llm_model_excel_plan == ""
    monkeypatch.setenv("LLM_MODEL_EXCEL_PLAN", "plan-model-y")
    assert Settings().llm_model_excel_plan == "plan-model-y"
