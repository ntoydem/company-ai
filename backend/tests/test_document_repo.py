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

from app.models.document import Confidentiality, Document, DocumentStatus, IngestionStatus
from app.models.document_page import DocumentPage
from app.models.project import Project
from app.repositories import document_repo
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


# --- Phase 3.2: mark_superseded status transition, metadata-suggestion queue/apply ---


def test_mark_superseded_transitions_lifecycle_statuses_to_superseded(db_session: Session) -> None:
    for status in (DocumentStatus.draft, DocumentStatus.executed, DocumentStatus.amended):
        older = _make_document(db_session)
        older.status = status
        newer = _make_document(db_session)
        db_session.commit()

        document_repo.mark_superseded(db_session, older=older, newer=newer)

        assert older.status == DocumentStatus.superseded
        assert older.superseded_by_document_id == newer.id


def test_mark_superseded_leaves_active_status_untouched(db_session: Session) -> None:
    """`active` is an operational, not lifecycle, state (docs/plans/PHASE_3_2_PLAN.md §6) —
    a document being superseded on paper doesn't stop being operationally active."""
    older = _make_document(db_session)
    older.status = DocumentStatus.active
    newer = _make_document(db_session)
    db_session.commit()

    document_repo.mark_superseded(db_session, older=older, newer=newer)

    assert older.status == DocumentStatus.active
    assert older.superseded_by_document_id == newer.id


def test_list_ids_pending_suggestion_only_returns_ready_without_suggestion(
    db_session: Session,
) -> None:
    ready_without_suggestion = _make_document(db_session)
    ready_without_suggestion.ingestion_status = IngestionStatus.ready
    ready_with_suggestion = _make_document(db_session)
    ready_with_suggestion.ingestion_status = IngestionStatus.ready
    ready_with_suggestion.ai_suggestion_id = uuid.uuid4()
    not_ready = _make_document(db_session)
    db_session.commit()

    result = document_repo.list_ids_pending_suggestion(db_session, limit=10)

    assert ready_without_suggestion.id in result
    assert ready_with_suggestion.id not in result
    assert not_ready.id not in result


def test_get_leading_page_text_joins_first_n_pages_in_order(db_session: Session) -> None:
    document = _make_document(db_session)
    db_session.flush()
    for page_number, text in ((1, "birinci sayfa"), (2, "ikinci sayfa"), (3, "üçüncü sayfa")):
        db_session.add(DocumentPage(document_id=document.id, page_number=page_number, text=text))
    db_session.commit()

    result = document_repo.get_leading_page_text(db_session, document.id, max_pages=2)

    assert result == "birinci sayfa\n\nikinci sayfa"


def test_apply_partial_update_writes_only_given_fields(db_session: Session) -> None:
    document = _make_document(db_session, department="finans")
    db_session.commit()
    original_title = document.title

    document_repo.apply_partial_update(db_session, document, {"department": "hukuk"})

    assert document.department == "hukuk"
    assert document.title == original_title
