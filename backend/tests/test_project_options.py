"""İş Emri 2026-10-17P1K (ADR-035, Tansu 16.10 madde 1): the options of the unnamed-value
project question are the projects holding the question's topic — decided per document,
inside `allowed` only (T-5). A single candidate is still asked (S-3); an undetermined topic
keeps every visible project (S-1); a topic in no project document asks nothing (S-2)."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.document import Document, DocumentStatus
from app.models.project import Project
from app.models.user import User
from app.schemas.ask import AskRequest
from app.services.ask import project_question_for
from app.services.project_narrowing import projects_with_data
from tests.department_fixtures import add_user_to_department, make_department
from tests.fakes import FakeLLMClient, FakeRouter
from tests.project_fixtures import ensure_projects
from tests.test_ask import _ask, _document

PROJECTS = (
    ("Karatepe RES", "ANK_RES"),
    ("Kızılova RES", "IZM_RES"),
    ("Boztepe RES", "BOZ_RES"),
    ("Yeşilova RES", "YSV_RES"),
)
INSURANCE = "Sigorta ne zaman bitiyor?"


@pytest.fixture(autouse=True)
def _ek_f_on(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ek_f_enabled", True)


@pytest.fixture
def projects(db_session: Session) -> dict[str, Project]:
    return ensure_projects(db_session, PROJECTS)


def _doc(
    session: Session,
    project: Project | None,
    text: str | None,
    *,
    title: str | None = None,
    department: str | None = None,
) -> Document:
    """A project (or, with None, group) document; `text=None` → no chunk (workbook-like)."""
    title = title or f"Belge {uuid.uuid4().hex[:6]}"
    if text is None:
        document = Document(
            title=title,
            document_type="financial_model",
            counterparty="Şirket içi",
            document_date=date(2026, 1, 1),
            department=department,
            status=DocumentStatus.executed,
            storage_path=f"{uuid.uuid4()}/original.xlsx",
        )
        session.add(document)
    else:
        document = _document(session, title=title, department=department, text=text)
    document.project_id = project.id if project else None
    session.commit()
    return document


def test_options_are_the_projects_holding_the_topic(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    projects: dict[str, Project],
) -> None:
    _doc(db_session, projects["ANK_RES"], "sigorta poliçesi bitiş tarihi")
    _doc(db_session, projects["IZM_RES"], "sigorta poliçesi yenileme")
    _doc(db_session, projects["BOZ_RES"], "kredi vade on yıl")
    _doc(db_session, projects["BOZ_RES"], "arazi edinimi")
    _doc(db_session, projects["ANK_RES"], "arazi edinimi")

    body = _ask(client, INSURANCE)

    assert fake_llm.requests == []
    assert body["answer"] == "Hangi proje için sormak istiyorsunuz (Karatepe RES, Kızılova RES)?"


def _enerji_user(session: Session, user: User) -> None:
    add_user_to_department(session, user, make_department(session, slug="enerji", name="Enerji"))


def test_hidden_document_never_becomes_an_option(
    client: TestClient,
    db_session: Session,
    employee_user: User,
    fake_llm: FakeLLMClient,
    projects: dict[str, Project],
) -> None:
    """T-5: Yeşilova's insurance endorsement sits in `finans`; the enerji user sees only
    Karatepe's insurance document and a Kızılova credit page."""
    _enerji_user(db_session, employee_user)
    make_department(db_session, slug="finans", name="Finans")
    _doc(db_session, projects["ANK_RES"], "sigorta poliçesi", department="enerji")
    _doc(db_session, projects["IZM_RES"], "kredi vade", department="enerji")
    hidden = _doc(db_session, projects["YSV_RES"], "sigorta zeyilnamesi", department="finans")

    body = _ask(client, INSURANCE)

    assert fake_llm.requests == []
    assert body["answer"] == "Hangi proje için sormak istiyorsunuz (Karatepe RES)?"
    assert "Yeşilova" not in body["answer"]
    assert str(hidden.id) not in body["retrieved_document_ids"]


def test_hidden_documents_do_not_make_a_term_generic(
    client: TestClient,
    db_session: Session,
    employee_user: User,
    fake_llm: FakeLLMClient,
    projects: dict[str, Project],
) -> None:
    """T-5, indirect: the generic share is taken from `allowed` only — piling up hidden
    insurance documents leaves the answer exactly as it was."""
    _enerji_user(db_session, employee_user)
    make_department(db_session, slug="hukuk", name="Hukuk")
    _doc(db_session, projects["ANK_RES"], "sigorta poliçesi", department="enerji")
    _doc(db_session, projects["IZM_RES"], "kredi vade", department="enerji")
    before = _ask(client, INSURANCE)["answer"]

    hidden = [
        _doc(db_session, projects[code], "sigorta poliçesi", department="hukuk")
        for code in ("IZM_RES", "BOZ_RES", "YSV_RES", "IZM_RES", "BOZ_RES")
    ]
    after = _ask(client, INSURANCE)

    assert fake_llm.requests == []
    assert before == after["answer"] == "Hangi proje için sormak istiyorsunuz (Karatepe RES)?"
    assert not {str(d.id) for d in hidden} & set(after["retrieved_document_ids"])


def test_single_candidate_is_still_asked(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    projects: dict[str, Project],
) -> None:
    _doc(db_session, projects["ANK_RES"], "sigorta poliçesi bitiş tarihi")
    _doc(db_session, projects["IZM_RES"], "kredi vade on yıl")

    body = _ask(client, INSURANCE)

    assert fake_router.questions == [] and fake_llm.requests == []
    assert body["answered"] is False and body["sources"] == []
    assert body["answer"] == "Hangi proje için sormak istiyorsunuz (Karatepe RES)?"


def test_topic_only_in_a_group_document_asks_no_project(
    db_session: Session, admin_user: User, fake_llm: FakeLLMClient, projects: dict[str, Project]
) -> None:
    """S-2: the best chunk is a project page ("zaman bitiyor") but the topic — sigorta — is
    only in a group document: no project question, the router decides as before."""
    docs = [
        _doc(db_session, None, "grup sigorta poliçesi"),
        _doc(db_session, projects["ANK_RES"], "zaman bitiyor zaman bitiyor"),
        _doc(db_session, projects["IZM_RES"], "kredi vade"),
    ]

    assert projects_with_data(db_session, {d.id for d in docs}, INSURANCE) == []
    request = AskRequest(question=INSURANCE)
    assert project_question_for(db_session, admin_user, request) is None
    assert fake_llm.requests == []


def test_topic_in_no_document_goes_to_the_router(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    projects: dict[str, Project],
) -> None:
    _doc(db_session, projects["ANK_RES"], "kredi vade on yıl")
    _doc(db_session, projects["IZM_RES"], "kredi vade sekiz yıl")

    body = _ask(client, INSURANCE)

    assert fake_router.questions == [INSURANCE]
    assert fake_llm.requests == []
    assert not body["answer"].startswith("Hangi proje için sormak istiyorsunuz")


def test_no_distinguishing_term_keeps_every_visible_project(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    projects: dict[str, Project],
) -> None:
    """S-1: every term is in more than half of the user's project documents."""
    for code in ("ANK_RES", "IZM_RES", "BOZ_RES"):
        _doc(db_session, projects[code], "kredi vade yıl")

    body = _ask(client, "Kredinin vadesi kaç yıl?")

    assert fake_llm.requests == []
    assert body["answer"] == (
        "Hangi proje için sormak istiyorsunuz (Boztepe RES, Karatepe RES, Kızılova RES)?"
    )


def test_catalogue_match_counts_for_a_document_without_chunks(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    projects: dict[str, Project],
) -> None:
    _doc(db_session, projects["BOZ_RES"], None, title="Boztepe DSCR Tablosu")
    _doc(db_session, projects["ANK_RES"], "dscr covenant test")
    _doc(db_session, projects["ANK_RES"], "arazi edinimi")
    _doc(db_session, projects["IZM_RES"], "kredi vade")
    _doc(db_session, projects["IZM_RES"], "arazi edinimi")

    body = _ask(client, "Güncel DSCR kaç?")

    assert fake_llm.requests == []
    assert body["answer"] == "Hangi proje için sormak istiyorsunuz (Boztepe RES, Karatepe RES)?"


def test_concept_term_outweighs_a_qualifier(
    db_session: Session, admin_user: User, projects: dict[str, Project]
) -> None:
    """ "son" is on a Yeşilova page, "tadil" only on Karatepe's: the concept decides."""
    docs = [
        _doc(db_session, projects["ANK_RES"], "tadil sözleşmesi amendment"),
        _doc(db_session, projects["YSV_RES"], "son ödeme tarihi"),
        _doc(db_session, projects["IZM_RES"], "arazi edinimi"),
        _doc(db_session, projects["BOZ_RES"], "arazi edinimi"),
    ]

    allowed = {d.id for d in docs}
    assert projects_with_data(db_session, allowed, "Son tadil neyi değiştirdi?") == ["Karatepe RES"]


def test_inactive_project_is_never_an_option(
    db_session: Session, admin_user: User, projects: dict[str, Project]
) -> None:
    projects["IZM_RES"].is_active = False
    docs = [
        _doc(db_session, projects["ANK_RES"], "sigorta poliçesi"),
        _doc(db_session, projects["IZM_RES"], "sigorta poliçesi"),
        _doc(db_session, projects["BOZ_RES"], "arazi edinimi"),
        _doc(db_session, projects["ANK_RES"], "arazi edinimi"),
    ]

    assert projects_with_data(db_session, {d.id for d in docs}, INSURANCE) == ["Karatepe RES"]
