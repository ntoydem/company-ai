"""İş Emri 2026-10-15A2L2 — two question shapes decided by code before any LLM call:

1. an unknown project ("Bursa RES") skips the router's classification call too, so the whole
   request runs with 0 LLM calls (A2L smoke (i): the router call was the only one left);
2. an existence / definition question ("… ne demek biliyor musun?", "… var mı?") is routed
   DOCUMENT by code and the answer model is never called — the F-3 grouped list plus one
   question is the reply, flag on and off alike (GEN-DSC-013, A2L smoke (e)).
"""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.document import Document
from app.models.project import Project
from app.models.user import User
from app.repositories import audit_log_repo
from app.services.answer_prompt import NO_ANSWER_TEXT, NO_DATA_VERDICT
from app.services.ask_router import route_without_llm
from app.services.assist import CLARIFY_TEMPLATE
from tests.fakes import FakeLLMClient, FakeRouter
from tests.project_fixtures import ensure_projects
from tests.test_ask import _ask, _document

_DEFINITION = re.compile(r"demektir|anlamına gel|ifade eder|olarak tanımlan", re.IGNORECASE)


@pytest.fixture
def ek_f_on(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ek_f_enabled", True)


@pytest.fixture
def assist_only(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "assist_mode_enabled", True)
    assert settings.ek_f_enabled is False


def _amendments(session: Session) -> tuple[Project, Document, Document]:
    project = ensure_projects(session)["ANK_RES"]
    first = _document(
        session,
        title="Facility Agreement Amendment 01",
        department=None,
        text="This amendment agreement modifies the repayment schedule of the facility.",
    )
    second = _document(
        session,
        title="Facility Agreement Amendment 02",
        department=None,
        text="This amendment agreement modifies the DSCR covenant and the margin.",
    )
    first.project_id = second.project_id = project.id
    session.commit()
    return project, first, second


def _last_audit_row(session: Session) -> tuple[str | None, int, int]:
    rows = audit_log_repo.list_filtered(session, limit=1)
    assert rows
    return rows[0].model, rows[0].tokens_in, rows[0].tokens_out


# ---------------------------------------------------------------- the pre-route itself


def test_route_without_llm_decides_only_its_shapes(db_session: Session) -> None:
    ensure_projects(db_session)
    unknown = route_without_llm(db_session, "Bursa RES'in kapasitesi nedir?")
    assert unknown is not None and unknown.reason == "unknown_project"
    assert unknown.query_type == "DOCUMENT_QUERY" and unknown.fallback_reason is None
    existence = route_without_llm(db_session, "Amendment ne demek biliyor musun?")
    assert existence is not None and existence.reason == "existence_question"
    assert existence.document_question == "Amendment ne demek biliyor musun?"
    # İş Emri 2026-10-16N1: an unnamed value question is the third shape.
    unnamed = route_without_llm(db_session, "DSCR nedir?")
    assert unnamed is not None and unnamed.reason == "unnamed_value_question"
    assert route_without_llm(db_session, "Karatepe RES'in kapasitesi nedir?") is None


def test_route_without_llm_leaves_fact_questions_to_the_router(db_session: Session) -> None:
    """İş Emri 2026-10-15A2L3: a fact asked with "var mı" or "hangisi" is a value question
    (ANK-FIN-004, IZM-DEV-004, ANK-EPC-002, GEN-CMP-003 shapes) — the router decides; only
    the document forms stay on the list path (GEN-DSC-005/009)."""
    ensure_projects(db_session)
    for question in (
        "Karatepe RES finansmanında ECA katılımı var mı?",
        "Kızılova RES'in yapı ruhsatı var mı?",
        "Karatepe RES'in güncel EPC sözleşmesi hangisi?",
        "Karatepe RES ile Kızılova RES'in kurulu gücü hangisi daha büyük?",
    ):
        assert route_without_llm(db_session, question) is None, question
    for question in ("Amendment var mı?", "Kredi sözleşmesinin son hali hangisi?"):
        routed = route_without_llm(db_session, question)
        assert routed is not None and routed.reason == "existence_question", question


# ---------------------------------------------------------------- 1. unknown project


@pytest.mark.parametrize("flag", ["ek_f_on", "assist_only"])
def test_unknown_project_makes_no_llm_call_at_all(
    flag: str,
    request: pytest.FixtureRequest,
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
) -> None:
    request.getfixturevalue(flag)
    _amendments(db_session)

    body = _ask(client, "Bursa RES'in kapasitesi nedir?")

    assert fake_router.questions == []  # the classification call is skipped too
    assert fake_llm.requests == []
    assert body["answered"] is False and body["sources"] == []
    assert body["model"] is None and body["tokens_in"] == 0 and body["tokens_out"] == 0
    assert body["assist"]["kind"] == "term_mismatch"
    assert body["assist"]["unmatched_terms"] == ["Bursa RES"]
    assert body["assist"]["question"].startswith("Bu adda bir proje kayıtlı değil")
    assert "router_fallback" not in {w["kind"] for w in body["warnings"]}
    assert _last_audit_row(db_session) == (None, 0, 0)


# ---------------------------------------------------------------- 2. existence questions


def test_definition_question_lists_documents_and_asks_without_any_llm_call(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    ek_f_on: None,
) -> None:
    """GEN-DSC-013 / A2L (e): no definition sentence can be composed because no model is
    asked; the project-headed list of the Amendment documents is the answer, one question
    closes it."""
    project, first, second = _amendments(db_session)
    fake_llm.replies = ["Amendment, sözleşme değişikliği anlamına gelir [K1]."]  # never used

    body = _ask(client, "Amendment ne demek biliyor musun?")

    assert fake_router.questions == [] and fake_llm.requests == []
    assert body["answered"] is False and body["sources"] == []
    assert body["model"] is None and body["tokens_in"] == 0 and body["tokens_out"] == 0
    assert body["query_type"] == "DOCUMENT_QUERY"
    answer: str = body["answer"]
    assert not _DEFINITION.search(answer)
    lines = answer.splitlines()
    assert NO_DATA_VERDICT in lines and "Elimde konuyla ilgili şunlar var:" in lines
    assert any(
        line.startswith(project.name) and first.title in line and second.title in line
        for line in lines
    )
    assert lines[-1] == CLARIFY_TEMPLATE and answer.count("?") == 1
    assist = body["assist"]
    assert assist["kind"] == "clarify" and assist["question"] == CLARIFY_TEMPLATE
    assert {a["title"] for a in assist["available"]} == {first.title, second.title}
    assert [g["project_code"] for g in assist["groups"]] == [project.code]
    assert body["retrieved_document_ids"]  # retrieval ran; only the model was skipped
    assert _last_audit_row(db_session) == (None, 0, 0)


def test_existence_question_without_ek_f_keeps_the_fixed_sentence_and_the_assist_block(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    assist_only: None,
) -> None:
    _, first, second = _amendments(db_session)

    body = _ask(client, "Amendment var mı?")

    assert fake_router.questions == [] and fake_llm.requests == []
    assert body["answer"] == NO_ANSWER_TEXT and body["answered"] is False
    assist = body["assist"]
    assert assist["kind"] == "clarify" and assist["groups"] == []
    assert {a["title"] for a in assist["available"]} == {first.title, second.title}


def test_existence_question_with_every_flag_off_is_the_fixed_sentence_alone(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    settings: Settings,
) -> None:
    assert settings.assist_computations is False
    _amendments(db_session)

    body = _ask(client, "Amendment var mı?")

    assert fake_router.questions == [] and fake_llm.requests == []
    assert body["answer"] == NO_ANSWER_TEXT and body["answered"] is False
    assert body["assist"] is None


def test_plain_definition_question_still_goes_through_router_and_model(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    ek_f_on: None,
) -> None:
    """ "DSCR nedir?" (GEN-GEN shape) is not an existence question: unchanged path — the
    router classifies, the documents are checked by the model."""
    _document(db_session, title="Facility Agreement", department=None, text="DSCR covenant 1,20")
    fake_llm.replies = ["DSCR covenant'ı 1,20 olarak belirlenmiştir [K1]."]

    body = _ask(client, "DSCR nedir?")

    assert fake_router.questions == ["DSCR nedir?"]
    assert len(fake_llm.requests) == 1
    assert body["answered"] is True and body["model"] == "fake-model"


def test_fact_question_with_var_mi_goes_through_router_and_model(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    ek_f_on: None,
) -> None:
    """İş Emri 2026-10-15A2L3 (ANK-FIN-004 shape): "ECA katılımı var mı?" expects a cited
    answer, not the document list — the normal path, flag on."""
    ensure_projects(db_session)
    _document(
        db_session,
        title="Facility Agreement",
        department=None,
        text="The facility includes an ECA covered tranche of 5,000,000 USD.",
    )
    fake_llm.replies = ["Evet, ECA katılımı vardır: 5.000.000 USD'lik ECA dilimi [K1]."]

    body = _ask(client, "Karatepe RES finansmanında ECA katılımı var mı?")

    assert fake_router.questions == ["Karatepe RES finansmanında ECA katılımı var mı?"]
    assert len(fake_llm.requests) == 1
    assert body["answered"] is True and body["model"] == "fake-model"


def test_existence_question_zero_chunks_still_lists_metadata_matches(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    ek_f_on: None,
) -> None:
    """The zero-chunk path (ADR-021) is unchanged by the pre-route: a title-only match is
    still listed, still without the LLM."""
    from tests.test_assist_ekf import _metadata_only

    project = ensure_projects(db_session)["ANK_RES"]
    workbook = _metadata_only(db_session, title="Financial Model 2026", project=project)

    body = _ask(client, "Finansal model var mı?")

    assert fake_router.questions == [] and fake_llm.requests == []
    assert body["answered"] is False
    assert [a["document_id"] for a in body["assist"]["available"]] == [str(workbook.id)]
