"""İş Emri 2026-10-17P2A (ADR-036, Tansu 17.10 madde 7/9/10): the Excel path's project scope.
A named project narrows the catalogue to its own (and group) workbooks; an unnamed question
whose data several projects hold gets one project question, no figure, no answering call;
one holder → answered with the project's name; two named → which one. Planner and answerer
are `FakeLLMClient`; the engine is the real `CachedValueEngine` over the demo workbooks."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.main import app
from app.models.document import Document
from app.models.project import Project
from app.models.user import User, UserRole
from app.repositories import user_repo
from app.services.answer_prompt import NO_ANSWER_TEXT
from app.services.excel_ask import ANSWER_SYSTEM_PROMPT, NO_DATA_TEXT, PLAN_SYSTEM_PROMPT
from app.services.llm import LLMRequest
from app.services.security import hash_password
from tests.department_fixtures import (
    add_user_to_department,
    make_department,
    make_department_manager,
)
from tests.fakes import FakeLLMClient, FakeRouter
from tests.project_fixtures import ensure_projects
from tests.test_excel_api import _publish, _upload_workbook

PROJECTS = (
    ("Karatepe RES", "ANK_RES"),
    ("Yeşilova RES", "YSV_RES"),
    ("Boztepe RES", "BOZ_RES"),
)
FINANCIAL_MODEL = ("Financial_Model_2026.xlsx", "Financial Model", "ANK_RES")
COVENANT = ("Covenant_Report.xlsx", "Covenant Report", "ANK_RES")
YESILOVA = ("Yesilova_Repayment_Schedule_2026-09.xlsx", "Repayment Schedule", "YSV_RES")
BOZTEPE = ("Boztepe_Repayment_Schedule_84_Instalments.xlsx", "Repayment Schedule", "BOZ_RES")

TODAY_DEBT = {"kind": "function", "name": "outstanding_debt", "params": {"as_of": "today"}}
DSCR = {"kind": "function", "name": "dscr", "params": {"period": "Q2_2026"}}
YSV_12 = {
    "kind": "sql",
    "sql": "SELECT anapara_usd FROM yesilova_repayment_schedule_2026_09__schedule "
    "WHERE taksit_no = 12",
    "future_ok": True,
}
KARATEPE_DEBT = "11.671.800"
SCHEDULE_QUESTION = "Hangi proje için sormak istiyorsunuz (Boztepe RES, Yeşilova RES)?"


@pytest.fixture
def projects(db_session: Session) -> dict[str, Project]:
    return ensure_projects(db_session, PROJECTS)


def _workbook(
    client: TestClient,
    session: Session,
    projects: dict[str, Project],
    spec: tuple[str, str, str | None],
    *,
    department: str | None = None,
) -> Document:
    file, document_type, code = spec
    body = _publish(session, _upload_workbook(client, file, department=department))
    document = session.get(Document, uuid.UUID(str(body["id"])))
    assert document is not None
    document.document_type = document_type
    document.project_id = projects[code].id if code else None
    session.commit()
    return document


def _all_workbooks(
    client: TestClient, session: Session, projects: dict[str, Project]
) -> dict[str, Document]:
    return {
        spec[0]: _workbook(client, session, projects, spec)
        for spec in (FINANCIAL_MODEL, COVENANT, YESILOVA, BOZTEPE)
    }


def _replies(plan: dict[str, object], answer: str = "-") -> list[str]:
    return [json.dumps(plan), answer]


def _excel_ask(client: TestClient, question: str) -> dict[str, object]:
    response = client.post("/api/excel/ask", json={"question": question})
    assert response.status_code == 200, response.text
    body: dict[str, object] = response.json()
    return body


def _plan_prompt(fake_llm: FakeLLMClient) -> str:
    return next(r.user for r in fake_llm.requests if r.system == PLAN_SYSTEM_PROMPT)


# ---------------------------------------------------------------- 1. named → narrowed


@pytest.mark.parametrize("plan", [TODAY_DEBT, DSCR], ids=["outstanding_debt", "dscr"])
def test_named_project_never_gets_another_projects_figure(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    projects: dict[str, Project],
    plan: dict[str, object],
) -> None:
    """Plan §1.3: "Yeşilova kalan kredi borcu" returned Karatepe's 11.671.800 USD; the
    Yeşilova catalogue has no Financial Model / Covenant Report → the function finds no
    data, the answering model is never called."""
    _all_workbooks(client, db_session, projects)
    fake_llm.replies = _replies(plan)

    body = _excel_ask(client, "Yeşilova RES'in kalan kredi borcu ne kadar?")

    assert body["answered"] is False and body["answer"] == NO_DATA_TEXT
    assert KARATEPE_DEBT not in str(body) and "1,37x" not in str(body)
    assert [r.system for r in fake_llm.requests] == [PLAN_SYSTEM_PROMPT]
    prompt = _plan_prompt(fake_llm)
    assert "yesilova_repayment_schedule_2026_09__schedule" in prompt
    for foreign in ("Financial_Model_2026", "Covenant_Report", "boztepe", "Boztepe"):
        assert foreign not in prompt


def test_named_project_reads_its_own_workbook(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    projects: dict[str, Project],
) -> None:
    _all_workbooks(client, db_session, projects)
    fake_llm.replies = _replies(YSV_12, "12. taksitin anaparası 98000.")

    body = _excel_ask(client, "Yeşilova RES ödeme planında 12. taksitin anaparası ne kadar?")

    assert body["answered"] is True and body["value"] == 98000
    assert body["excel_files"] == ["Yesilova_Repayment_Schedule_2026-09.xlsx"]
    assert body["answer"] == "12. taksitin anaparası 98000."  # named: no prefix added


def test_karatepe_question_is_unchanged(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    projects: dict[str, Project],
) -> None:
    """The Karatepe figure stays exactly what it was; only the other projects' tables
    leave the catalogue."""
    _all_workbooks(client, db_session, projects)
    fake_llm.replies = _replies(TODAY_DEBT, f"Kalan borç {KARATEPE_DEBT} USD.")

    body = _excel_ask(client, "Karatepe RES'in kalan kredi borcu ne kadar?")

    assert body["answered"] is True and body["value"] == 11671800
    assert body["excel_files"] == ["Financial_Model_2026.xlsx"]
    assert body["answer"] == f"Kalan borç {KARATEPE_DEBT} USD."
    prompt = _plan_prompt(fake_llm)
    assert "financial_model_2026__debt" in prompt and "covenant_report" in prompt
    assert "yesilova" not in prompt and "boztepe" not in prompt


def test_named_project_keeps_group_workbooks(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    projects: dict[str, Project],
) -> None:
    """A group workbook (`project_id` NULL) is in scope for every project (ADR-031)."""
    _workbook(client, db_session, projects, ("Covenant_Report.xlsx", "Covenant Report", None))
    _workbook(client, db_session, projects, FINANCIAL_MODEL)
    fake_llm.replies = _replies(DSCR, "DSCR 1,37x.")

    body = _excel_ask(client, "Yeşilova RES'in DSCR değeri kaç?")

    assert body["answered"] is True and body["excel_files"] == ["Covenant_Report.xlsx"]
    assert "financial_model" not in _plan_prompt(fake_llm)


# ---------------------------------------------------------------- 2. unnamed, several holders


def test_unnamed_question_held_by_two_projects_asks_which_project(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    projects: dict[str, Project],
) -> None:
    _all_workbooks(client, db_session, projects)
    fake_llm.replies = _replies(YSV_12)

    body = _excel_ask(client, "Ödeme planında 12. taksitin anaparası ne kadar?")

    assert body["answered"] is False and body["answer"] == SCHEDULE_QUESTION
    assert body["value"] is None and body["sources"] == [] and body["excel_files"] == []
    assert [r.system for r in fake_llm.requests] == [PLAN_SYSTEM_PROMPT]  # no answering call
    assert "98000" not in str(body) and "98.000" not in str(body)


def test_unnamed_project_question_through_api_ask_does_not_fall_back(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    projects: dict[str, Project],
) -> None:
    _all_workbooks(client, db_session, projects)
    fake_router.query_type = "DATA_QUERY"
    fake_llm.replies = _replies(YSV_12)

    response = client.post("/api/ask", json={"question": "Ödeme planında 12. taksitin anaparası"})

    body = response.json()
    assert body["query_type"] == "DATA_QUERY" and body["answered"] is False
    assert body["answer"] == SCHEDULE_QUESTION
    assert body["assist"]["kind"] == "disambiguate"
    assert body["assist"]["question"] == SCHEDULE_QUESTION
    assert [r.system for r in fake_llm.requests] == [PLAN_SYSTEM_PROMPT]
    assert body["excel_sources"] == [] and body["sources"] == []


def test_mixed_with_both_halves_asking_shows_one_question(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    projects: dict[str, Project],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Plan §8: a MIXED call whose document half asks the project too shows one question."""
    from app.services import ask_router
    from app.services.ask import AskResult
    from app.services.assist import build_unnamed_project_assist

    _all_workbooks(client, db_session, projects)
    fake_router.query_type = "MIXED_QUERY"
    document_question = "Hangi proje için sormak istiyorsunuz (Karatepe RES, Yeşilova RES)?"

    def fake_document_half(*args: object, **kwargs: object) -> AskResult:
        return AskResult(
            answer=document_question,
            answered=False,
            assist=build_unnamed_project_assist(document_question),
        )

    monkeypatch.setattr(ask_router, "answer_question", fake_document_half)
    fake_llm.replies = _replies(YSV_12)

    body = client.post("/api/ask", json={"question": "12. taksitin anaparası ve vadesi"}).json()

    assert body["answer"] == document_question and body["answered"] is False
    assert body["answer"].count("Hangi proje") == 1


# ---------------------------------------------------------------- 3. unnamed, one holder


def test_unnamed_question_with_one_holder_is_answered_with_the_project_name(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    projects: dict[str, Project],
) -> None:
    """Madde 9: only Karatepe holds a Financial Model → answered, project name + card."""
    _all_workbooks(client, db_session, projects)
    fake_llm.replies = _replies(TODAY_DEBT, f"Kalan kredi borcu {KARATEPE_DEBT} USD.")

    body = _excel_ask(client, "Kalan kredi borcu ne kadar?")

    assert body["answered"] is True
    assert body["answer"] == f"Karatepe RES: Kalan kredi borcu {KARATEPE_DEBT} USD."
    assert body["sources"][0]["file"] == "Financial_Model_2026.xlsx"  # type: ignore[index]


def test_answer_already_naming_the_project_is_not_prefixed(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    projects: dict[str, Project],
) -> None:
    _all_workbooks(client, db_session, projects)
    fake_llm.replies = _replies(TODAY_DEBT, f"Karatepe RES kalan borcu {KARATEPE_DEBT} USD.")

    body = _excel_ask(client, "Kalan kredi borcu ne kadar?")

    assert body["answer"] == f"Karatepe RES kalan borcu {KARATEPE_DEBT} USD."


def test_group_workbook_result_is_answered_without_question_or_prefix(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    projects: dict[str, Project],
) -> None:
    _workbook(client, db_session, projects, ("Covenant_Report.xlsx", "Covenant Report", None))
    _workbook(client, db_session, projects, YESILOVA)
    fake_llm.replies = _replies(DSCR, "DSCR 1,37x.")

    body = _excel_ask(client, "Güncel DSCR kaç?")

    assert body["answered"] is True and body["answer"] == "DSCR 1,37x."


# ---------------------------------------------------------------- 4. two projects named


def test_two_named_projects_ask_which_one(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    projects: dict[str, Project],
) -> None:
    _all_workbooks(client, db_session, projects)
    fake_llm.replies = _replies(YSV_12)

    body = _excel_ask(client, "Yeşilova RES ve Boztepe RES'in 12. taksit anaparası ne kadar?")

    assert body["answered"] is False and body["answer"] == SCHEDULE_QUESTION
    assert [r.system for r in fake_llm.requests] == [PLAN_SYSTEM_PROMPT]
    prompt = _plan_prompt(fake_llm)
    assert "financial_model" not in prompt and "covenant_report" not in prompt


# ---------------------------------------------------------------- 5. authorization (T-5)


def _enerji_employee(session: Session) -> User:
    enerji = make_department(session, slug="enerji_grubu")
    make_department_manager(session, enerji, username="enerji_mgr")
    employee = user_repo.create(
        session,
        username="enerji_p2a",
        password_hash=hash_password("x"),
        display_name="Enerji",
        role=UserRole.employee,
    )
    add_user_to_department(session, employee, enerji)
    return employee


def _as(user: User, admin: User, client: TestClient, path: str, question: str) -> dict[str, object]:
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        response = client.post(path, json={"question": question})
    finally:
        app.dependency_overrides[get_current_user] = lambda: admin
    assert response.status_code == 200, response.text
    body: dict[str, object] = response.json()
    return body


def test_hidden_workbook_is_never_in_the_catalogue_or_the_options(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    projects: dict[str, Project],
) -> None:
    """Yeşilova/Boztepe schedules sit in `finans`; the enerji user sees Karatepe's
    production workbook only. No hidden table, file name or project reaches the planner,
    the answer or the options."""
    finans = make_department(db_session, slug="finans")
    make_department_manager(db_session, finans)
    employee = _enerji_employee(db_session)
    _workbook(
        client,
        db_session,
        projects,
        ("Monthly_Production_2026.xlsx", "Monthly Production", "ANK_RES"),
        department="enerji_grubu",
    )
    for spec in (YESILOVA, BOZTEPE):
        _workbook(client, db_session, projects, spec, department="finans")
    fake_llm.replies = _replies(YSV_12)

    body = _as(employee, admin_user, client, "/api/excel/ask", "12. taksitin anaparası kaç?")

    assert body["answered"] is False
    prompt = _plan_prompt(fake_llm)
    # `plan` echoes the fake planner's own SQL (a real planner never saw the table); what
    # the user is shown — answer, cards, files — carries nothing of the hidden workbooks.
    shown = str([body["answer"], body["sources"], body["excel_files"], body["value"]])
    for hidden in ("yesilova", "Yesilova", "boztepe", "Boztepe", "Repayment"):
        assert hidden not in prompt
        assert hidden not in shown
    assert "Yeşilova" not in shown and "98000" not in shown


def test_hidden_holders_do_not_change_the_result(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    projects: dict[str, Project],
) -> None:
    """A hidden workbook of the same type in another project must not turn the visible
    single holder into a project question (indirect leak): the enerji user still gets
    the Karatepe answer with "Karatepe RES:"."""
    finans = make_department(db_session, slug="finans")
    make_department_manager(db_session, finans)
    employee = _enerji_employee(db_session)
    production = ("Monthly_Production_2026.xlsx", "Monthly Production")
    _workbook(client, db_session, projects, (*production, "ANK_RES"), department="enerji_grubu")
    plan = {"kind": "function", "name": "production", "params": {"period": "2026-06"}}

    fake_llm.replies = _replies(plan)
    before = _as(employee, admin_user, client, "/api/excel/ask", "Haziran 2026 üretimi kaç?")
    for code in ("YSV_RES", "BOZ_RES"):
        _workbook(client, db_session, projects, (*production, code), department="finans")
    fake_llm.replies = _replies(plan)
    after = _as(employee, admin_user, client, "/api/excel/ask", "Haziran 2026 üretimi kaç?")

    assert before["answered"] is True and str(before["answer"]).startswith("Karatepe RES: ")
    assert after["answer"] == before["answer"] and after["value"] == before["value"]
    assert "Yeşilova" not in str(after) and "Boztepe" not in str(after)


def test_planner_prompt_of_every_call_carries_only_allowed_files(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    projects: dict[str, Project],
) -> None:
    """Every request the fake LLM received (plan + answer) is free of the other projects'
    workbook names for a named question."""
    _all_workbooks(client, db_session, projects)
    fake_llm.replies = _replies(DSCR, "DSCR 1,37x.")

    _excel_ask(client, "Karatepe RES'in güncel DSCR değeri kaç?")

    def text(request: LLMRequest) -> str:
        return request.system + request.user

    assert [r.system for r in fake_llm.requests] == [PLAN_SYSTEM_PROMPT, ANSWER_SYSTEM_PROMPT]
    for request in fake_llm.requests:
        assert "Yesilova" not in text(request) and "Boztepe" not in text(request)
    assert NO_ANSWER_TEXT not in text(fake_llm.requests[-1])
