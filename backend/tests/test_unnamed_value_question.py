"""İş Emri 2026-10-16N1 (Tansu 16.10, madde 7): a question that names no project.

- a *value* question (a figure, a date, a condition) → code asks one sentence, "Hangi proje
  için sormak istiyorsunuz?", with only the user's own projects in brackets; no router call,
  no answer model, no list;
- a *discovery* question ("var mı", "nerede", "neler") → the F-3 grouped list, unchanged;
- a named project, an explicit "her proje için ayrı ayrı" / a question about the projects
  themselves, a follow-up whose previous question named the project, and a company question
  (best chunk is a group document) → today's path, unchanged.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.document import Document
from app.models.project import Project
from app.models.user import User
from app.repositories import audit_log_repo
from app.services.answer_prompt import NO_ANSWER_TEXT
from app.services.ask_router import route_without_llm
from app.services.project_narrowing import (
    UNNAMED_PROJECT_QUESTION,
    asks_across_projects,
    is_unnamed_value_question,
    unnamed_project_question,
)
from tests.fakes import FakeLLMClient, FakeRouter
from tests.project_fixtures import ensure_projects
from tests.test_ask import _ask, _document

PROJECTS = (("Karatepe RES", "ANK_RES"), ("Kızılova RES", "IZM_RES"), ("Boztepe RES", "BOZ_RES"))
VALUE_QUESTION = "Kredinin vadesi kaç yıl?"


@pytest.fixture
def ek_f_on(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ek_f_enabled", True)


@pytest.fixture
def ek_f_off(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ek_f_enabled", False)
    monkeypatch.setattr(settings, "assist_mode_enabled", False)


def _projects(session: Session) -> dict[str, Project]:
    return ensure_projects(session, PROJECTS)


def _project_documents(session: Session, department: str | None = None) -> list[Document]:
    """One credit page per project, all matching "kredi vade" — no group document."""
    projects = _projects(session)
    docs = []
    for code, label in (("ANK_RES", "on"), ("IZM_RES", "sekiz"), ("BOZ_RES", "yedi")):
        doc = _document(
            session,
            title=f"{code} Kredi Sözleşmesi",
            department=department,
            text=f"kredi vade {label} yıl",
        )
        doc.project_id = projects[code].id
        docs.append(doc)
    session.commit()
    return docs


def _last_audit_row(session: Session) -> tuple[str | None, int, int]:
    rows = audit_log_repo.list_filtered(session, limit=1)
    assert rows
    return rows[0].model, rows[0].tokens_in, rows[0].tokens_out


# ---------------------------------------------------------------- the classifier


def test_value_questions_without_a_project_are_recognised(db_session: Session) -> None:
    _projects(db_session)
    for question in (
        VALUE_QUESTION,
        "Güncel DSCR kaç?",
        "Lisans ne zaman alındı?",
        "Sözleşmenin vadesi ne zaman doluyor?",
        "ÇED tamamlandı mı?",
        "Lisans durumu ne?",
    ):
        assert is_unnamed_value_question(db_session, question), question
        routed = route_without_llm(db_session, question)
        assert routed is not None and routed.reason == "unnamed_value_question", question
        assert routed.query_type == "DOCUMENT_QUERY" and routed.fallback_reason is None


def test_other_shapes_are_not_unnamed_value_questions(db_session: Session) -> None:
    _projects(db_session)
    for question in (
        "Kredi sözleşmesi var mı?",  # discovery → existence path (F-3 list)
        "ÇED raporu nerede?",
        "Karatepe RES'in kredi vadesi kaç yıl?",  # named
        "Bursa RES'in kapasitesi nedir?",  # unknown project → its own refusal
        "Her proje için ayrı ayrı kredi vadesi kaç yıl?",  # explicit per-project request
        "Proje proje kredi vadeleri nedir?",
        "Hangi projenin üretim lisansı var?",  # the project is the subject
        "Tüm projelerin kapasitesi nedir?",
        "Şirketin genel müdürü kim?",  # the company, not a project
        "teşekkürler",  # not a question
    ):
        assert not is_unnamed_value_question(db_session, question), question
    assert asks_across_projects("Her bir proje için ayrı ayrı yazar mısın?")
    assert route_without_llm(db_session, "Her proje için ayrı ayrı kredi vadesi kaç yıl?") is None


def test_previous_question_naming_a_project_keeps_the_follow_up_on_todays_path(
    db_session: Session,
) -> None:
    _projects(db_session)
    previous = "Karatepe RES'in kredi tutarı nedir?"
    assert not is_unnamed_value_question(db_session, "Vadesi ne zaman?", previous)
    assert route_without_llm(db_session, "Vadesi ne zaman?", previous) is None
    assert is_unnamed_value_question(db_session, "Vadesi ne zaman?", "Teşekkürler.")


def test_the_one_sentence() -> None:
    assert unnamed_project_question([]) == UNNAMED_PROJECT_QUESTION
    assert unnamed_project_question(["Boztepe RES", "Karatepe RES"]) == (
        "Hangi proje için sormak istiyorsunuz (Boztepe RES, Karatepe RES)?"
    )


# ---------------------------------------------------------------- end to end


def test_unnamed_value_question_is_one_sentence_without_any_llm_call(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    ek_f_on: None,
) -> None:
    docs = _project_documents(db_session)

    body = _ask(client, VALUE_QUESTION)

    assert fake_router.questions == [] and fake_llm.requests == []
    assert body["answered"] is False and body["sources"] == []
    assert body["model"] is None and body["tokens_in"] == 0 and body["tokens_out"] == 0
    answer: str = body["answer"]
    assert answer.startswith("Hangi proje için sormak istiyorsunuz (")
    assert "\n" not in answer and answer.count("?") == 1
    assert all(name in answer for name, _ in PROJECTS)
    assist = body["assist"]
    assert assist["kind"] == "disambiguate" and assist["question"] == answer
    assert assist["available"] == [] and assist["groups"] == []
    assert set(body["retrieved_document_ids"]) == {str(d.id) for d in docs}
    assert _last_audit_row(db_session) == (None, 0, 0)


def test_unnamed_value_question_with_flags_off_keeps_the_fixed_sentence_first(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    ek_f_off: None,
) -> None:
    """Flag-independent policy (ADR-032 ilke 1): flag off, the same question follows the
    fixed sentence — as on the unknown-project path (ADR-031)."""
    _project_documents(db_session)

    body = _ask(client, VALUE_QUESTION)

    assert fake_router.questions == [] and fake_llm.requests == []
    question = body["assist"]["question"]
    assert body["answer"] == f"{NO_ANSWER_TEXT}\n{question}"
    assert question.startswith("Hangi proje için sormak istiyorsunuz (")


def test_projects_outside_the_gate_are_never_named(
    client: TestClient,
    db_session: Session,
    employee_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    ek_f_on: None,
) -> None:
    """T-5/G3: an employee of `finans` sees only Karatepe's document — Kızılova and Boztepe
    are outside the gate and must not appear in the question."""
    from tests.department_fixtures import add_user_to_department, make_department

    projects = _projects(db_session)
    finans = make_department(db_session, slug="finans", name="Finans")
    add_user_to_department(db_session, employee_user, finans)
    visible = _document(db_session, title="Karatepe FA", department="finans", text="kredi vade")
    hidden = _document(db_session, title="Kızılova FA", department="hukuk", text="kredi vade")
    visible.project_id, hidden.project_id = projects["ANK_RES"].id, projects["IZM_RES"].id
    db_session.commit()

    body = _ask(client, VALUE_QUESTION)

    assert fake_llm.requests == []
    assert body["answer"] == "Hangi proje için sormak istiyorsunuz (Karatepe RES)?"
    assert str(hidden.id) not in body["retrieved_document_ids"]


def test_unnamed_discovery_question_keeps_the_grouped_list(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    ek_f_on: None,
) -> None:
    docs = _project_documents(db_session)

    body = _ask(client, "Kredi sözleşmesi var mı?")

    assert fake_router.questions == [] and fake_llm.requests == []
    assert "Elimde konuyla ilgili şunlar var:" in body["answer"].splitlines()
    assert body["assist"]["kind"] == "clarify"
    assert {a["title"] for a in body["assist"]["available"]} == {d.title for d in docs}
    assert len(body["assist"]["groups"]) == 3


def test_named_question_is_unchanged(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    ek_f_on: None,
) -> None:
    _project_documents(db_session)
    fake_llm.replies = ["Kredinin vadesi on yıldır [K1]."]

    body = _ask(client, "Karatepe RES kredisinin vadesi kaç yıl?")

    assert fake_router.questions == ["Karatepe RES kredisinin vadesi kaç yıl?"]
    assert len(fake_llm.requests) == 1
    assert body["answered"] is True


def test_explicit_per_project_request_keeps_todays_path(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    ek_f_on: None,
) -> None:
    """ "Her proje için ayrı ayrı" is Ürün 2's per-project answer, not built here: the router
    and the pipeline run exactly as before this order (here the Adım 4 axis decides)."""
    _project_documents(db_session)
    question = "Her proje için ayrı ayrı kredi vadesi kaç yıl?"

    body = _ask(client, question)

    assert fake_router.questions == [question]
    assert not body["answer"].startswith("Hangi proje için sormak istiyorsunuz")


def test_company_question_goes_through_router_and_model(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    ek_f_on: None,
) -> None:
    """CO-NEG-005 shape: the best chunk is a group (company) document — there is no project
    to ask about, so the router and the model run as before."""
    projects = _projects(db_session)
    _document(
        db_session,
        title="Yönetim Kurulu Kararı — Denetim Komitesi Ataması",
        department=None,
        text="denetim komitesi üyeleri yönetim kurulu kararı ile atandı denetim komitesi",
    )
    project_doc = _document(db_session, title="Saha Notu", department=None, text="komitesi")
    project_doc.project_id = projects["ANK_RES"].id
    db_session.commit()
    question = "Denetim komitesi üyeleri hangi kararla atandı?"
    fake_llm.replies = ["Yönetim kurulu kararı ile atandı [K1]."]

    body = _ask(client, question)

    assert fake_router.questions == [question]
    assert len(fake_llm.requests) == 1
    assert body["answered"] is True


def test_no_visible_project_goes_through_router_and_model(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    ek_f_on: None,
) -> None:
    """Only group documents in the gate: no project to ask about → today's path."""
    _projects(db_session)
    _document(db_session, title="Grup Kredi Politikası", department=None, text="kredi vade on yıl")
    fake_llm.replies = ["Vade on yıldır [K1]."]

    _ask(client, VALUE_QUESTION)

    assert fake_router.questions == [VALUE_QUESTION]
    assert len(fake_llm.requests) == 1


def test_follow_up_to_a_named_question_keeps_todays_path(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    ek_f_on: None,
) -> None:
    _project_documents(db_session)
    fake_llm.replies = ["Kredinin vadesi on yıldır [K1]."]

    _ask(client, "Vadesi kaç yıl?", previous_question="Karatepe RES kredisinin tutarı nedir?")

    assert fake_router.questions == ["Vadesi kaç yıl?"]
