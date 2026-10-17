"""İş Emri 2026-10-17P2B (ADR-037, plan §3.2 a/c, §8): the router's repayment-schedule hint,
the planner's version sentence, project + version status on the catalogue line, and the
leak test — for the enerji, hukuk and finans users every prompt the fake LLM receives is
free of the workbooks that user may not see."""

from __future__ import annotations

import json
import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.excel.calc import QueryResult
from app.models.document import Document, DocumentStatus
from app.models.project import Project
from app.models.user import User, UserRole
from app.repositories import user_repo
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.authorization import AuthorizationScope
from app.services.authorization import allowed_document_ids
from app.services.excel_ask import (
    PLAN_SYSTEM_PROMPT,
    _sql_value,
    _workbook_line,
    format_value,
)
from app.services.router import ROUTER_SYSTEM_PROMPT, LLMRouter
from app.services.security import hash_password
from tests.department_fixtures import (
    add_user_to_department,
    make_department,
    make_department_manager,
)
from tests.fakes import FakeLLMClient, FakeRouter
from tests.test_excel_project_scope import (
    BOZTEPE,
    FINANCIAL_MODEL,
    YESILOVA,
    _as,
    _excel_ask,
    _plan_prompt,
    _workbook,
    projects,  # noqa: F401  (fixture)
)

YESILOVA_OLD = ("Yesilova_Repayment_Schedule_2026-03.xlsx", "Repayment Schedule", "YSV_RES")
PRODUCTION = ("Monthly_Production_2026.xlsx", "Monthly Production", "ANK_RES")
NONE_PLAN = json.dumps({"kind": "none", "reason": "test"})

# ---------------------------------------------------------------- prompts (plan §3.2 a/c)

ROUTER_EXCEL = (
    "monthly production, loan repayment schedules (ödeme planı: instalment number, due date, "
    "principal, interest per instalment); figures computed by a calculation engine."
)
ROUTER_DATA = (
    "A value read from a repayment schedule row — an instalment's (taksit) due date (vade), "
    "principal (anapara) or interest, the next or a numbered instalment — is DATA_QUERY, even "
    "when the question says 'ödeme planında'. Only repayment terms written in a loan agreement "
    "(tenor, agreed number of instalments, grace period) are DOCUMENT_QUERY."
)
ROUTER_EXAMPLE = (
    'Q: Ödeme planında 5. taksitin vadesi ne? -> {"query_type":"DATA_QUERY",'
    '"document_question":null,"data_question":null,"reason":"repayment schedule row"}'
)
PLAN_VERSION = (
    "Use the current version of a workbook; use a superseded one only when the question names "
    "that older version or date."
)


def test_router_prompt_carries_the_two_sentences_and_one_generic_example() -> None:
    """Tansu 17.10 madde 7: the plan's 2 sentences + 1 example without a project name."""
    assert ROUTER_EXCEL in ROUTER_SYSTEM_PROMPT
    assert ROUTER_DATA in ROUTER_SYSTEM_PROMPT
    assert ROUTER_EXAMPLE in ROUTER_SYSTEM_PROMPT
    assert ROUTER_SYSTEM_PROMPT.count("taksit") == 2  # the DATA sentence + the example
    for name in ("Yeşilova", "Boztepe", "Yesilova", "12. taksit", "98.000"):
        assert name not in ROUTER_SYSTEM_PROMPT


def test_plan_prompt_carries_the_version_sentence_once() -> None:
    assert PLAN_SYSTEM_PROMPT.endswith(PLAN_VERSION)
    assert PLAN_SYSTEM_PROMPT.count("superseded") == 1


def test_router_request_is_the_static_prompt_and_the_question_only(settings: Settings) -> None:
    fake = FakeLLMClient(['{"query_type":"DATA_QUERY"}'])
    routed = LLMRouter(fake, settings).route("Ödeme planında 12. taksitin anaparası ne kadar?")
    assert routed.query_type == "DATA_QUERY"
    (request,) = fake.requests
    assert request.system == ROUTER_SYSTEM_PROMPT
    assert request.user == "Q: Ödeme planında 12. taksitin anaparası ne kadar?"


# ---------------------------------------------------------------- catalogue line (§3.2c)


def _document(
    title: str, status: DocumentStatus, project: Project | None, newer: uuid.UUID | None = None
) -> Document:
    return Document(
        id=uuid.uuid4(),
        title=title,
        document_type="Repayment Schedule",
        status=status,
        project=project,
        superseded_by_document_id=newer,
    )


def test_catalogue_line_names_project_status_and_the_newer_file() -> None:
    project = Project(name="Yeşilova RES", code="YSV_RES")
    current = _document("Ödeme Planı — Güncel", DocumentStatus.active, project)
    old = _document("Ödeme Planı — Mart 2026", DocumentStatus.superseded, project, current.id)
    files = {current.id: "Yesilova_Repayment_Schedule_2026-09.xlsx", old.id: "old.xlsx"}

    assert _workbook_line(current, files[current.id], files) == (
        "- file: Yesilova_Repayment_Schedule_2026-09.xlsx (title: Ödeme Planı — Güncel, "
        "type: Repayment Schedule, project: Yeşilova RES, status: active)"
    )
    assert _workbook_line(old, "old.xlsx", files) == (
        "- file: old.xlsx (title: Ödeme Planı — Mart 2026, type: Repayment Schedule, "
        "project: Yeşilova RES, status: superseded, superseded by: "
        "Yesilova_Repayment_Schedule_2026-09.xlsx)"
    )
    group = _document("Grup bütçesi", DocumentStatus.active, None)
    assert "project: group, status: active)" in _workbook_line(group, "g.xlsx", {})


def test_newer_file_outside_the_catalogue_is_not_named() -> None:
    """T-5: `superseded by` comes only from the (authorized, narrowed) catalogue."""
    old = _document("Eski", DocumentStatus.superseded, None, uuid.uuid4())
    line = _workbook_line(old, "old.xlsx", {old.id: "old.xlsx"})
    assert line.endswith("status: superseded)") and "superseded by" not in line


def test_planner_sees_status_and_superseded_by_for_the_yesilova_pair(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    projects: dict[str, Project],  # noqa: F811
) -> None:
    current = _workbook(client, db_session, projects, YESILOVA)
    old = _workbook(client, db_session, projects, YESILOVA_OLD)
    current.status = DocumentStatus.active  # as the seed manifest sets it
    old.status = DocumentStatus.superseded
    old.superseded_by_document_id = current.id
    db_session.commit()
    fake_llm.replies = [NONE_PLAN]

    _excel_ask(client, "Yeşilova RES ödeme planında 12. taksitin anaparası ne kadar?")

    prompt = _plan_prompt(fake_llm)
    assert (
        "project: Yeşilova RES, status: superseded, superseded by: "
        "Yesilova_Repayment_Schedule_2026-09.xlsx)" in prompt
    )
    assert "project: Yeşilova RES, status: active)" in prompt
    # ADR-037 header row: the planner sees the real columns, not `col_b`
    assert "'taksit_no', 'vade', 'anapara_usd', 'faiz_usd'" in prompt
    assert "col_b" not in prompt


@pytest.mark.parametrize("ek_f", [False, True])
def test_a_typed_due_date_is_formatted_not_a_server_error(ek_f: bool) -> None:
    """Before ADR-037 `vade` was text; as a date the pre-Ek-F path raised `float(datetime)`
    (found by the P2B eval measure)."""
    result = QueryResult(("vade",), ((datetime(2026, 10, 14),),), (), False)
    value, unit, _ = _sql_value(result, ek_f=ek_f)
    assert (value, unit) == ("14.10.2026", "")
    assert format_value(value, unit, ek_f=ek_f) == "14.10.2026"


def test_yesilova_instalment_cells_through_the_pipeline(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    projects: dict[str, Project],  # noqa: F811
) -> None:
    """B-01 example 1 / 3 cells with the real header: number, date, project's own file."""
    _workbook(client, db_session, projects, YESILOVA)
    table = "yesilova_repayment_schedule_2026_09__schedule"
    fake_llm.replies = [
        json.dumps({"kind": "sql", "sql": f"SELECT anapara_usd FROM {table} WHERE taksit_no = 12"}),
        "-",
        json.dumps({"kind": "sql", "sql": f"SELECT vade FROM {table} WHERE taksit_no = 11"}),
        "-",
    ]

    principal = _excel_ask(client, "Yeşilova RES ödeme planında 12. taksitin anaparası ne kadar?")
    due = _excel_ask(client, "Yeşilova RES ödeme planında 11. taksitin vadesi ne?")

    assert principal["answered"] is True and principal["value"] == 98000
    assert principal["formatted_value"] == "98.000"
    assert due["answered"] is True and due["formatted_value"] == "14.10.2026"
    assert principal["excel_files"] == due["excel_files"] == [YESILOVA[0]]


# ---------------------------------------------------------------- leak test (§8 item 2)


def _member(session: Session, slug: str) -> User:
    user = user_repo.create(
        session,
        username=f"{slug}_p2b",
        password_hash=hash_password("x"),
        display_name=slug,
        role=UserRole.employee,
    )
    department = make_department(session, slug=slug)
    make_department_manager(session, department, username=f"{slug}_mgr")
    add_user_to_department(session, user, department)
    return user


def _hidden_names(document: Document) -> list[str]:
    stem = document.file_name.rsplit(".", 1)[0]
    return [document.file_name, stem, stem.lower().replace("-", "_"), document.title]


@pytest.mark.parametrize("slug", ["enerji_grubu", "hukuk", "finans"])
def test_no_prompt_carries_a_workbook_the_user_may_not_see(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    projects: dict[str, Project],  # noqa: F811
    slug: str,
) -> None:
    users = {s: _member(db_session, s) for s in ("enerji_grubu", "hukuk", "finans")}
    workbooks = [
        _workbook(client, db_session, projects, PRODUCTION, department="enerji_grubu"),
        *(
            _workbook(client, db_session, projects, spec, department="finans")
            for spec in (FINANCIAL_MODEL, YESILOVA, YESILOVA_OLD, BOZTEPE)
        ),
    ]
    user = users[slug]
    allowed = allowed_document_ids(user, AuthorizationScope(), SqlDocumentIdsProvider(db_session))
    hidden = [d for d in workbooks if d.id not in allowed]
    assert hidden, "every user must have hidden workbooks for this test to mean anything"
    fake_router.query_type = "DATA_QUERY"
    fake_llm.reply_fn = lambda request: NONE_PLAN

    for path, question in (
        ("/api/excel/ask", "Ödeme planında 12. taksitin anaparası ne kadar?"),
        ("/api/excel/ask", "Yeşilova RES'in bir sonraki taksiti ne zaman?"),
        ("/api/ask", "Boztepe RES ödeme planında 12. taksitin anaparası ne kadar?"),
        ("/api/ask", "Haziran 2026 üretimi kaç?"),
    ):
        _as(user, admin_user, client, path, question)

    prompts = [r.system + "\n" + r.user for r in fake_llm.requests]
    for document in hidden:
        for name in _hidden_names(document):
            for prompt in prompts:
                assert name not in prompt, (slug, name)
