"""Şart 1 — project narrowing (İş Emri 2026-10-15A2, ADR-031): after the gate, a question
that names a project sees that project's documents plus group documents and nothing else —
in the prompt, in the F-3 list and in the audit row; an unknown project is refused without
the LLM; an unnamed question is untouched (Adım 4 axis as before). Flag on and off alike."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.db import get_engine
from app.models.audit_log import AuditLog
from app.models.document import Document, DocumentStatus, IngestionStatus, ProjectScope
from app.models.project import Project
from app.models.user import User
from app.repositories import audit_log_repo
from app.services import project_narrowing as narrowing
from app.services.answer_prompt import NO_ANSWER_TEXT, NO_DATA_VERDICT
from tests.conftest import alembic_config
from tests.fakes import FakeLLMClient, FakeRouter
from tests.test_ask import _ask, _document


@pytest.fixture
def ek_f_on(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ek_f_enabled", True)


@pytest.fixture
def ek_f_off(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ek_f_enabled", False)
    monkeypatch.setattr(settings, "assist_mode_enabled", False)


def _projects(session: Session) -> dict[str, Project]:
    rows = {
        "ANK_RES": Project(name="Karatepe RES", code="ANK_RES"),
        "IZM_RES": Project(name="Kızılova RES", code="IZM_RES"),
        "BOZ_RES": Project(name="Boztepe RES", code="BOZ_RES"),
    }
    session.add_all(rows.values())
    session.commit()
    return rows


def _corpus(session: Session) -> dict[str, Document]:
    """Three projects' pages on the same subject plus one group (company-level) page —
    every page matches the FTS query "kredi vade", so retrieval alone keeps them all."""
    projects = _projects(session)
    docs = {
        "ank": _document(
            session, title="Karatepe Kredi Sözleşmesi", department=None, text="kredi vade on yıl"
        ),
        "izm": _document(
            session, title="Kızılova Kredi Sözleşmesi", department=None, text="kredi vade sekiz yıl"
        ),
        "boz": _document(
            session, title="Boztepe Kredi Sözleşmesi", department=None, text="kredi vade yedi yıl"
        ),
        "grp": _document(
            session, title="Grup Kredi Politikası", department=None, text="kredi vade politikası"
        ),
    }
    docs["ank"].project_id = projects["ANK_RES"].id
    docs["izm"].project_id = projects["IZM_RES"].id
    docs["boz"].project_id = projects["BOZ_RES"].id
    session.commit()
    for key, doc in docs.items():
        session.refresh(doc)
        assert doc.project_scope == (ProjectScope.group if key == "grp" else ProjectScope.project)
    return docs


def _last_audit(session: Session) -> AuditLog:
    rows = audit_log_repo.list_filtered(session, limit=1)
    assert rows
    return rows[0]


# ---------------------------------------------------------------- model + migration


def test_project_scope_follows_project_id_on_insert_and_update(db_session: Session) -> None:
    projects = _projects(db_session)
    doc = _document(db_session, title="X", department=None, text="t")
    assert doc.project_scope == ProjectScope.group  # NULL project_id → group
    doc.project_id = projects["ANK_RES"].id
    db_session.commit()
    db_session.refresh(doc)
    assert doc.project_scope == ProjectScope.project
    doc.project_id = None
    db_session.commit()
    db_session.refresh(doc)
    assert doc.project_scope == ProjectScope.group


def test_0016_backfills_group_adds_the_check_and_downgrades_cleanly() -> None:
    cfg = alembic_config()
    engine = get_engine()
    command.downgrade(cfg, "0015")
    assert "project_scope" not in {c["name"] for c in inspect(engine).get_columns("documents")}
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM documents"))
        conn.execute(text("DELETE FROM projects"))
        conn.execute(
            text(
                "INSERT INTO projects (id, name, code, stage, is_active, created_at, updated_at) "
                "VALUES ('11111111-1111-1111-1111-111111111111', 'Karatepe RES', 'ANK_RES', "
                "'operation', true, now(), now())"
            )
        )
        for title, project in (
            ("grup", "NULL"),
            ("proje", "'11111111-1111-1111-1111-111111111111'"),
        ):
            conn.execute(
                text(
                    "INSERT INTO documents (id, title, document_type, counterparty, document_date, "
                    "status, department, project_id, storage_path, ingestion_status, source, "
                    "confidentiality, tags, related_document_ids, version) VALUES "
                    f"(gen_random_uuid(), '{title}', 't', 'c', '2026-01-01', 'executed', 'finans', "
                    f"{project}, 'x/original.pdf', 'ready', 'web', 'normal', '{{}}', '{{}}', 1)"
                )
            )
    command.upgrade(cfg, "head")
    with engine.connect() as conn:
        scopes = dict(conn.execute(text("SELECT title, project_scope::text FROM documents")).all())
    assert scopes == {"grup": "group", "proje": "project"}
    # the CHECK rejects an inconsistent pair written around the ORM
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(text("UPDATE documents SET project_scope = 'project' WHERE title = 'grup'"))
    command.downgrade(cfg, "0015")
    with engine.connect() as conn:
        types = conn.execute(text("SELECT typname FROM pg_type WHERE typname = 'project_scope'"))
        assert types.first() is None
    command.upgrade(cfg, "head")


# ---------------------------------------------------------------- pure helpers


def test_unknown_project_names_reads_the_projects_table(db_session: Session) -> None:
    _projects(db_session)
    assert narrowing.unknown_project_names(db_session, "Bursa RES'in kapasitesi nedir?") == [
        "Bursa RES"
    ]
    assert narrowing.unknown_project_names(db_session, "Manisa GES'in COD tarihi?") == [
        "Manisa GES"
    ]
    # known projects, determiners and question words are not unknown projects
    assert narrowing.unknown_project_names(db_session, "Karatepe RES'in kapasitesi nedir?") == []
    assert narrowing.unknown_project_names(db_session, "Hangi RES projesinin lisansı var?") == []
    assert narrowing.unknown_project_names(db_session, "Bu RES için ÇED tamamlandı mı?") == []
    assert narrowing.unknown_project_names(db_session, "res kelimesi geçen cümle") == []
    # a renamed project's old name is unknown too — the table is the single source
    assert narrowing.unknown_project_names(db_session, "Ankara RES'in lisansı?") == ["Ankara RES"]


def test_unknown_project_question_names_only_visible_projects() -> None:
    q = narrowing.unknown_project_question
    assert q(["Bursa RES"], []) == "Bu adda bir proje kayıtlı değil; hangi projeyi kastediyorsunuz?"
    assert q(["Bursa RES"], ["Karatepe RES"]).endswith("Karatepe RES projesini mi kastediyorsunuz?")
    assert q(["Bursa RES"], ["Karatepe RES", "Kızılova RES"]) == (
        "Bu adda bir proje kayıtlı değil; hangi projeyi kastediyorsunuz: "
        "Karatepe RES mi, Kızılova RES mi?"
    )
    three = q(["Bursa RES"], ["A RES", "B RES", "C RES"])
    assert three.endswith("A RES, B RES yoksa C RES mi?") and not any(ch.isdigit() for ch in three)


def test_narrow_allowed_keeps_named_projects_and_group_documents(db_session: Session) -> None:
    docs = _corpus(db_session)
    allowed = {d.id for d in docs.values()}
    one = narrowing.narrow_allowed(db_session, allowed, ["ANK_RES"])
    assert one.active and one.scoped == {docs["ank"].id, docs["grp"].id} and one.dropped == 2
    two = narrowing.narrow_allowed(db_session, allowed, ["ANK_RES", "IZM_RES"])
    assert two.scoped == {docs["ank"].id, docs["izm"].id, docs["grp"].id}
    none = narrowing.narrow_allowed(db_session, allowed, [])
    assert not none.active and none.scoped == frozenset(allowed) and none.dropped == 0
    # the gate comes first: a document outside `allowed` never enters the scoped set
    partial = narrowing.narrow_allowed(db_session, {docs["izm"].id}, ["ANK_RES"])
    assert partial.scoped == frozenset()


# ---------------------------------------------------------------- /api/ask, flag on and off


@pytest.mark.parametrize("flag", ["ek_f_on", "ek_f_off"])
def test_named_project_question_narrows_prompt_list_and_audit(
    flag: str,
    request: pytest.FixtureRequest,
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
) -> None:
    request.getfixturevalue(flag)
    docs = _corpus(db_session)
    fake_llm.replies = [NO_ANSWER_TEXT]

    body = _ask(client, "Karatepe RES kredisinin vadesi kaç yıl?")

    prompt = fake_llm.prompt_text(0)
    assert "on yıl" in prompt and "politikası" in prompt  # named project + group document
    assert "sekiz yıl" not in prompt and "yedi yıl" not in prompt  # other projects: gone
    retrieved = set(body["retrieved_document_ids"])
    assert retrieved == {str(docs["ank"].id), str(docs["grp"].id)}
    row = _last_audit(db_session)
    audited = {c["document_id"] for c in row.chunks_retrieved}
    assert audited == {str(docs["ank"].id), str(docs["grp"].id)}
    if flag == "ek_f_on":
        listed = {a["document_id"] for a in body["assist"]["available"]}
        assert str(docs["izm"].id) not in listed and str(docs["boz"].id) not in listed
        assert str(docs["ank"].id) in listed
        scopes = {a["document_id"]: a["project_scope"] for a in body["assist"]["available"]}
        assert scopes.get(str(docs["grp"].id), "group") == "group"
        assert "Kızılova" not in body["answer"] and "Boztepe" not in body["answer"]


def test_two_named_projects_narrow_to_both_plus_group(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    ek_f_on: None,
) -> None:
    docs = _corpus(db_session)
    fake_llm.replies = [NO_ANSWER_TEXT]

    body = _ask(client, "Karatepe RES ile Kızılova RES kredilerinin vadesi kaç yıl?")

    prompt = fake_llm.prompt_text(0)
    assert "on yıl" in prompt and "sekiz yıl" in prompt and "politikası" in prompt
    assert "yedi yıl" not in prompt
    assert str(docs["boz"].id) not in body["retrieved_document_ids"]
    assert (body["assist"] or {}).get("kind") != "disambiguate"


def test_unnamed_question_is_untouched_and_keeps_the_axis_decision(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    ek_f_on: None,
) -> None:
    """No project named → no narrowing: every project's page is still a candidate and the
    Adım 4 axis decides (here an even three-way split → `disambiguate`, no LLM)."""
    docs = _corpus(db_session)

    body = _ask(client, "Kredinin vadesi kaç yıl?")

    assert fake_llm.requests == []
    assert body["assist"]["kind"] == "disambiguate"
    assert set(body["retrieved_document_ids"]) == {str(d.id) for d in docs.values()}


def test_answered_source_cards_carry_project_scope(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    ek_f_off: None,
) -> None:
    docs = _corpus(db_session)
    fake_llm.replies = ["Vade on yıldır [K1]; grup politikası da bunu teyit eder [K2]."]

    body = _ask(client, "Karatepe RES kredisinin vadesi kaç yıl?")

    assert body["answered"] is True
    by_id = {s["document_id"]: s for s in body["sources"]}
    assert {
        by_id[str(docs["ank"].id)]["project_scope"],
        by_id[str(docs["grp"].id)]["project_scope"],
    } == {
        "project",
        "group",
    }


@pytest.mark.parametrize("flag", ["ek_f_on", "ek_f_off"])
def test_unknown_project_is_refused_without_the_llm(
    flag: str,
    request: pytest.FixtureRequest,
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
) -> None:
    request.getfixturevalue(flag)
    _corpus(db_session)

    body = _ask(client, "Bursa RES'in kredi vadesi kaç yıl?")

    assert fake_llm.requests == []  # no retrieval package reaches the model, no guess
    assert body["answered"] is False and body["sources"] == []
    assert body["retrieved_document_ids"] == []
    assist = body["assist"]
    assert assist["kind"] == "term_mismatch" and assist["unmatched_terms"] == ["Bursa RES"]
    assert assist["available"] == [] and "varsayıldı" not in body["answer"]
    question = assist["question"]
    assert question.startswith("Bu adda bir proje kayıtlı değil")
    assert "Boztepe RES" in question and "Karatepe RES" in question and "Kızılova RES" in question
    assert not any(ch.isdigit() for ch in question)
    verdict = NO_DATA_VERDICT if flag == "ek_f_on" else NO_ANSWER_TEXT
    assert body["answer"] == f"{verdict}\n{question}"
    row = _last_audit(db_session)
    assert row.chunks_retrieved == [] and row.assist["kind"] == "term_mismatch"


def test_unknown_project_question_offers_only_the_projects_the_user_can_see(
    client: TestClient,
    db_session: Session,
    employee_user: User,
    fake_llm: FakeLLMClient,
    ek_f_on: None,
) -> None:
    """An employee of `finans` sees only Karatepe's finance document — the question must not
    name Kızılova or Boztepe (G3), whose documents are outside the gate."""
    from tests.department_fixtures import add_user_to_department, make_department

    projects = _projects(db_session)
    finans = make_department(db_session, slug="finans", name="Finans")
    add_user_to_department(db_session, employee_user, finans)
    visible = _document(db_session, title="Karatepe FA", department="finans", text="kredi vade")
    hidden = _document(db_session, title="Kızılova FA", department="hukuk", text="kredi vade")
    visible.project_id, hidden.project_id = projects["ANK_RES"].id, projects["IZM_RES"].id
    db_session.commit()

    body = _ask(client, "Bursa RES kredisinin vadesi kaç yıl?")

    question = body["assist"]["question"]
    assert "Karatepe RES" in question and "Kızılova RES" not in question
    assert "Boztepe" not in question


def test_mixed_sub_question_uses_the_users_wording_for_the_project(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
    ek_f_on: None,
) -> None:
    """The router may rewrite the document sub-question without the project name; the
    narrowing still reads the project from what the user typed (`original_question`)."""
    docs = _corpus(db_session)
    fake_router.query_type = "MIXED_QUERY"
    fake_router.document_question = "Kredinin vadesi kaç yıl?"
    fake_router.data_question = "DSCR kaç?"
    fake_llm.replies = [NO_ANSWER_TEXT, NO_ANSWER_TEXT, NO_ANSWER_TEXT]

    body = _ask(client, "Karatepe RES kredisinin vadesi kaç yıl ve güncel DSCR kaç?")

    assert str(docs["izm"].id) not in body["retrieved_document_ids"]
    assert str(docs["boz"].id) not in body["retrieved_document_ids"]
    assert (body["assist"] or {}).get("kind") != "disambiguate"


def _ready_group_document(session: Session, title: str) -> Document:
    document = Document(
        title=title,
        document_type="Politika",
        counterparty="c",
        document_date=date(2024, 6, 1),
        status=DocumentStatus.executed,
        storage_path=f"{uuid.uuid4()}/original.xlsx",
        ingestion_status=IngestionStatus.ready,
    )
    session.add(document)
    session.commit()
    return document


def test_zero_chunk_named_question_lists_only_the_named_project_and_group(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    ek_f_on: None,
) -> None:
    """Metadata-only candidates (workbooks) follow the same narrowing: the other project's
    title match is not a candidate; the group document stays."""
    projects = _projects(db_session)
    grp = _ready_group_document(db_session, "Bütçe Politikası")
    other = _ready_group_document(db_session, "Kızılova Bütçe Tablosu")
    other.project_id = projects["IZM_RES"].id
    mine = _ready_group_document(db_session, "Karatepe Bütçe Tablosu")
    mine.project_id = projects["ANK_RES"].id
    db_session.commit()

    body = _ask(client, "Karatepe RES bütçe dosyası var mı?")

    assert fake_llm.requests == []
    listed = {a["document_id"] for a in body["assist"]["available"]}
    assert str(mine.id) in listed and str(grp.id) in listed and str(other.id) not in listed
    assert "Kızılova" not in body["answer"]
