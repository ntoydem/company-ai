"""SQL-level filtering for `SqlDocumentIdsProvider` (ADR-007).

Repo-level unit tests only: `department`/`project_id` here are plain free-text/UUID
columns on `documents` with synthetic rows, not real per-user department membership
(the `departments`/`user_departments` tables, and `allowed_document_ids`'s real rules,
only arrive in Phase 1.2). Full integration coverage of "this user only sees their own
department" is deferred to that phase's test suite.
"""

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.document import Confidentiality, Document
from app.models.project import Project
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.authorization import AuthorizationScope


def _make_document(
    session: Session,
    *,
    department: str | None = None,
    project_id: uuid.UUID | None = None,
    confidentiality: Confidentiality = Confidentiality.normal,
) -> Document:
    document = Document(
        title="t",
        document_type="dt",
        counterparty="c",
        document_date=date(2023, 1, 1),
        storage_path=f"{uuid.uuid4()}/original.pdf",
        department=department,
        project_id=project_id,
        confidentiality=confidentiality,
    )
    session.add(document)
    session.flush()
    return document


def _make_project(session: Session, *, code: str) -> Project:
    project = Project(name=code, code=code)
    session.add(project)
    session.flush()
    return project


def test_list_document_ids_filters_by_department_at_sql_level(db_session: Session) -> None:
    finance_doc = _make_document(db_session, department="finance")
    legal_doc = _make_document(db_session, department="legal")
    db_session.commit()

    result = set(
        SqlDocumentIdsProvider(db_session).list_document_ids(
            AuthorizationScope(department="finance")
        )
    )

    assert finance_doc.id in result
    assert legal_doc.id not in result


def test_list_document_ids_filters_by_project_id_at_sql_level(db_session: Session) -> None:
    project = _make_project(db_session, code="ANK_RES")
    other_project = _make_project(db_session, code="IZM_RES")
    matching = _make_document(db_session, project_id=project.id)
    other = _make_document(db_session, project_id=other_project.id)
    db_session.commit()

    result = set(
        SqlDocumentIdsProvider(db_session).list_document_ids(
            AuthorizationScope(project_id=project.id)
        )
    )

    assert matching.id in result
    assert other.id not in result


def test_list_document_ids_with_no_scope_returns_all(db_session: Session) -> None:
    first = _make_document(db_session, department="finance")
    second = _make_document(db_session, department="legal")
    db_session.commit()

    result = set(SqlDocumentIdsProvider(db_session).list_document_ids(AuthorizationScope()))

    assert {first.id, second.id} <= result


def test_list_document_ids_for_departments_filters_by_department_and_confidentiality(
    db_session: Session,
) -> None:
    normal_finans = _make_document(db_session, department="finans")
    restricted_finans = _make_document(
        db_session, department="finans", confidentiality=Confidentiality.restricted
    )
    normal_hukuk = _make_document(db_session, department="hukuk")
    db_session.commit()

    result = set(
        SqlDocumentIdsProvider(db_session).list_document_ids_for_departments(
            department_slugs=["finans"], confidentiality_levels=[Confidentiality.normal]
        )
    )

    assert result == {normal_finans.id}
    assert restricted_finans.id not in result
    assert normal_hukuk.id not in result


def test_list_document_ids_for_departments_with_none_slugs_covers_every_department(
    db_session: Session,
) -> None:
    a = _make_document(db_session, department="finans")
    b = _make_document(db_session, department="hukuk")
    db_session.commit()

    result = set(
        SqlDocumentIdsProvider(db_session).list_document_ids_for_departments(
            department_slugs=None, confidentiality_levels=[Confidentiality.normal]
        )
    )

    assert {a.id, b.id} <= result
