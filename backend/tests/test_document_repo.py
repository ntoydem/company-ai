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

from app.models.document import Document
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.authorization import AuthorizationScope


def _make_document(
    session: Session, *, department: str | None = None, project_id: uuid.UUID | None = None
) -> Document:
    document = Document(
        title="t",
        document_type="dt",
        counterparty="c",
        document_date=date(2023, 1, 1),
        storage_path=f"{uuid.uuid4()}/original.pdf",
        department=department,
        project_id=project_id,
    )
    session.add(document)
    session.flush()
    return document


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
    project_id = uuid.uuid4()
    matching = _make_document(db_session, project_id=project_id)
    other = _make_document(db_session, project_id=uuid.uuid4())
    db_session.commit()

    result = set(
        SqlDocumentIdsProvider(db_session).list_document_ids(
            AuthorizationScope(project_id=project_id)
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
