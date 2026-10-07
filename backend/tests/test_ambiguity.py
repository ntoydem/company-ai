"""Adım 2 (BELIRSIZLIK_PLAN option 2, Naci 07.10.2026): code-side ambiguity detection on the
DOCUMENT_QUERY path, behind ASSIST_MODE — no LLM call when it fires, fixed templates only,
names only from the retrieved (allowed) documents."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.audit_log import AuditLog
from app.models.document import Document, DocumentStatus, IngestionStatus
from app.models.document_chunk import DocumentChunk
from app.models.project import Project
from app.models.user import User
from app.services import ambiguity
from app.services.answer_prompt import NO_ANSWER_TEXT, SYSTEM_PROMPT
from tests.fakes import FakeLLMClient, FakeRouter
from tests.test_ask import _ask


@pytest.fixture
def assist_on(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "assist_mode_enabled", True)


def _project(session: Session, name: str, code: str) -> Project:
    project = Project(name=name, code=code)
    session.add(project)
    session.commit()
    return project


def _doc(
    session: Session,
    *,
    title: str,
    document_type: str,
    text: str,
    project: Project | None = None,
) -> Document:
    document = Document(
        title=title,
        document_type=document_type,
        counterparty="c",
        document_date=date(2024, 1, 1),
        status=DocumentStatus.executed,
        storage_path=f"{uuid.uuid4()}/original.pdf",
        project_id=project.id if project else None,
        ingestion_status=IngestionStatus.ready,  # keep Not 7's pending check out of the way
    )
    session.add(document)
    session.flush()
    session.add(DocumentChunk(document_id=document.id, chunk_index=0, page_number=1, text=text))
    session.commit()
    return document


def _two_projects_two_licences(session: Session) -> tuple[Document, Document]:
    ankara = _project(session, "Ankara RES", "ANK_RES")
    izmir = _project(session, "İzmir RES", "IZM_RES")
    a = _doc(
        session,
        title="Ankara RES Üretim Lisansı",
        document_type="Üretim Lisansı",
        text="Üretim lisansı 15.06.2020 tarihinde onaylanmıştır; lisans süresi 49 yıl.",
        project=ankara,
    )
    b = _doc(
        session,
        title="İzmir RES Önlisans Belgesi",
        document_type="Önlisans",
        text=(
            "Önlisans 18.01.2024 tarihinde düzenlenmiştir; lisans aşaması için üretim "
            "lisansı başvurusu hazırlanıyor."
        ),
        project=izmir,
    )
    return a, b


def test_scope_less_question_on_two_projects_asks_which_project_without_llm(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    a, b = _two_projects_two_licences(db_session)

    body = _ask(client, "Lisans ne zaman alındı?")

    assert fake_llm.requests == []  # detected before the model is called
    assert body["answered"] is False and body["answer"] == NO_ANSWER_TEXT  # ADR-014
    assist = body["assist"]
    assert assist["kind"] == "clarify" and assist["axis"] == "project"
    assert assist["question"] == "Hangi projeyi kastediyorsunuz: Ankara RES mi, İzmir RES mi?"
    assert {x["document_id"] for x in assist["available"]} == {str(a.id), str(b.id)}
    assert (body["tokens_in"], body["model"]) == (0, None)
    row = db_session.scalars(select(AuditLog)).one()
    assert row.assist["axis"] == "project" and row.assist["kind"] == "clarify"


def test_named_project_is_not_ambiguous(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    _two_projects_two_licences(db_session)
    fake_llm.replies = ["Ankara RES lisansı 15.06.2020 tarihinde onaylanmıştır [K1]."]

    body = _ask(client, "Ankara RES üretim lisansı ne zaman alındı?")

    assert len(fake_llm.requests) == 1
    assert body["answered"] is True and body["assist"] is None


def test_list_request_is_not_ambiguous(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    _two_projects_two_licences(db_session)
    fake_llm.replies = ["Ankara 15.06.2020 [K1]. İzmir 18.01.2024 [K2]."]

    body = _ask(client, "Tüm lisanslar ne zaman alındı?")

    assert len(fake_llm.requests) == 1 and body["answered"] is True


def test_single_group_is_not_ambiguous(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    ankara = _project(db_session, "Ankara RES", "ANK_RES")
    _doc(
        db_session,
        title="Ankara RES Üretim Lisansı",
        document_type="Üretim Lisansı",
        text="Lisans 15.06.2020 tarihinde onaylanmıştır.",
        project=ankara,
    )
    _doc(
        db_session,
        title="Licence Amendment 01",
        document_type="Üretim Lisansı",  # same family → one group (a version chain)
        text="Lisans kapasitesi 60 MW olarak tadil edilmiştir.",
        project=ankara,
    )
    fake_llm.replies = ["Lisans 15.06.2020 tarihinde onaylanmıştır [K1]."]

    body = _ask(client, "Lisans ne zaman alındı?")

    assert len(fake_llm.requests) == 1 and body["answered"] is True


def test_two_document_families_in_one_project_ask_which_document(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    co = _project(db_session, "Ankara RES", "ANK_RES")
    _doc(
        db_session,
        title="Facility Agreement Amendment 02",
        document_type="Facility Agreement",
        text="Tadil ile geri ödeme planı değiştirilmiştir; tadil 20.02.2026 tarihlidir.",
        project=co,
    )
    _doc(
        db_session,
        title="Licence Amendment 01 (Kapasite Tadili)",
        document_type="Üretim Lisansı",
        text="Tadil ile kapasite 48 MW'tan 60 MW'a çıkarılmıştır; tadil 10.02.2021 tarihlidir.",
        project=co,
    )

    body = _ask(client, "Son tadil neyi değiştirdi?")

    assert fake_llm.requests == []
    assist = body["assist"]
    assert assist["axis"] == "document"
    assert assist["question"].startswith("Hangi belgeyi kastediyorsunuz: ")
    assert "Facility Agreement Amendment 02" in assist["question"]
    assert "Licence Amendment 01 (Kapasite Tadili)" in assist["question"]


def test_mixed_query_skips_the_check(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_router: FakeRouter,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    _two_projects_two_licences(db_session)
    fake_router.query_type = "MIXED_QUERY"
    fake_llm.replies = ["Ankara 15.06.2020 [K1]. İzmir 18.01.2024 [K2]."]

    body = _ask(client, "Lisans ne zaman alındı?")

    assert body["query_type"] == "MIXED_QUERY"
    assert fake_llm.requests, "the model was called — no code-side clarify on MIXED"
    assert body["assist"] is None  # answered: nothing to clarify


def test_flag_off_is_byte_identical(
    client: TestClient, db_session: Session, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    _two_projects_two_licences(db_session)
    fake_llm.replies = ["Ankara 15.06.2020 [K1]. İzmir 18.01.2024 [K2]."]

    body = _ask(client, "Lisans ne zaman alındı?")

    assert len(fake_llm.requests) == 1 and fake_llm.requests[0].system == SYSTEM_PROMPT
    assert body["answered"] is True and body["assist"] is None


def test_names_come_only_from_retrieved_allowed_documents(db_session: Session) -> None:
    """G3: the template is built from the retrieved documents' own titles/projects; a
    document outside `documents` (the allowed, retrieved set) can never be named."""
    a, b = _two_projects_two_licences(db_session)
    hidden = _doc(
        db_session,
        title="Gizli Lisans",
        document_type="Lisans",
        text="gizli lisans metni",
    )
    chunks = db_session.scalars(select(DocumentChunk)).all()
    from app.repositories.document_chunk_repo import RetrievedChunk

    retrieved = [
        RetrievedChunk(
            id=c.id,
            document_id=c.document_id,
            chunk_index=c.chunk_index,
            page_number=c.page_number,
            text=c.text,
            rank=1.0,
        )
        for c in chunks
        if c.document_id != hidden.id
    ]
    found = ambiguity.detect(
        db_session, {a.id, b.id}, "Lisans ne zaman alındı?", retrieved, {a.id: a, b.id: b}
    )
    assert found is not None and "Gizli" not in found.question
    assert {d.id for d in found.documents} == {a.id, b.id}


def test_naming_the_document_type_is_scope(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    assist_on: None,
) -> None:
    """Plan exclusion (b): "Üretim lisansı ne zaman alındı?" names a candidate's type even
    though "lisansı" is a class word (dry-run false positive ANK-NEG-004) → no clarify."""
    _two_projects_two_licences(db_session)
    fake_llm.replies = ["Üretim lisansı 15.06.2020 tarihinde onaylanmıştır [K1]."]

    body = _ask(client, "Üretim lisansı ne zaman alındı?")

    assert len(fake_llm.requests) == 1 and body["answered"] is True
