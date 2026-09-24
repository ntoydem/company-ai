"""`audit_log_repo` (Phase 3.4, SPEC_06 §1)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories import audit_log_repo


def _create(session: Session, *, user_id: uuid.UUID | None = None, **overrides: object) -> AuditLog:
    defaults: dict[str, object] = {
        "user_id": user_id,
        "question": "Ankara RES'in güncel DSCR'ı nedir?",
        "query_type": "DOCUMENT_QUERY",
        "scope_department": "finans",
        "scope_project": None,
        "documents_retrieved": [],
        "answer": "1,20x [K1].",
        "sources": [{"ref": "K1", "title": "Facility Agreement"}],
        "model": "gemini-3.5-flash-lite",
        "tokens_in": 100,
        "tokens_out": 20,
        "cost_estimate": None,
        "execution_ms": 500,
        "request_id": "req-1",
        "error": None,
    }
    defaults.update(overrides)
    return audit_log_repo.create(session, **defaults)


def test_create_persists_all_fields(db_session: Session, admin_user: User) -> None:
    row = _create(db_session, user_id=admin_user.id)

    fetched = audit_log_repo.get(db_session, row.id)
    assert fetched is not None
    assert fetched.user_id == admin_user.id
    assert fetched.question == "Ankara RES'in güncel DSCR'ı nedir?"
    assert fetched.sources == [{"ref": "K1", "title": "Facility Agreement"}]
    assert fetched.cost_estimate is None
    assert fetched.error is None


def test_get_unknown_id_returns_none(db_session: Session) -> None:
    assert audit_log_repo.get(db_session, uuid.uuid4()) is None


def test_list_filtered_by_user_id(
    db_session: Session, admin_user: User, employee_user: User
) -> None:
    mine = _create(db_session, user_id=admin_user.id)
    _create(db_session, user_id=employee_user.id)

    rows = audit_log_repo.list_filtered(db_session, user_id=admin_user.id)

    assert [r.id for r in rows] == [mine.id]


def test_list_filtered_by_department_and_project(db_session: Session, admin_user: User) -> None:
    project_id = uuid.uuid4()
    finans = _create(db_session, user_id=admin_user.id, scope_department="finans")
    _create(db_session, user_id=admin_user.id, scope_department="hukuk")
    scoped = _create(
        db_session, user_id=admin_user.id, scope_department=None, scope_project=project_id
    )

    assert [r.id for r in audit_log_repo.list_filtered(db_session, department="finans")] == [
        finans.id
    ]
    assert [r.id for r in audit_log_repo.list_filtered(db_session, project_id=project_id)] == [
        scoped.id
    ]


def test_list_filtered_by_has_error(db_session: Session, admin_user: User) -> None:
    ok = _create(db_session, user_id=admin_user.id, error=None)
    failed = _create(db_session, user_id=admin_user.id, error="LLM rate limited")

    assert [r.id for r in audit_log_repo.list_filtered(db_session, has_error=True)] == [failed.id]
    assert [r.id for r in audit_log_repo.list_filtered(db_session, has_error=False)] == [ok.id]


def test_list_filtered_by_date_range_and_ordering(db_session: Session, admin_user: User) -> None:
    older = _create(db_session, user_id=admin_user.id)
    newer = _create(db_session, user_id=admin_user.id)
    older.timestamp = datetime.now(UTC) - timedelta(days=10)
    newer.timestamp = datetime.now(UTC)
    db_session.commit()

    rows = audit_log_repo.list_filtered(db_session, from_ts=datetime.now(UTC) - timedelta(days=1))

    assert [r.id for r in rows] == [newer.id]  # newest first, older excluded by from_ts


def test_list_filtered_limit_and_offset(db_session: Session, admin_user: User) -> None:
    for _ in range(3):
        _create(db_session, user_id=admin_user.id)

    page1 = audit_log_repo.list_filtered(db_session, limit=2, offset=0)
    page2 = audit_log_repo.list_filtered(db_session, limit=2, offset=2)

    assert len(page1) == 2
    assert len(page2) == 1
    assert {r.id for r in page1}.isdisjoint({r.id for r in page2})


def test_delete_older_than_removes_only_stale_rows(db_session: Session, admin_user: User) -> None:
    old = _create(db_session, user_id=admin_user.id)
    recent = _create(db_session, user_id=admin_user.id)
    old.timestamp = datetime.now(UTC) - timedelta(days=91)
    recent.timestamp = datetime.now(UTC) - timedelta(days=1)
    db_session.commit()

    deleted = audit_log_repo.delete_older_than(db_session, datetime.now(UTC) - timedelta(days=90))

    assert deleted == 1
    assert audit_log_repo.get(db_session, old.id) is None
    assert audit_log_repo.get(db_session, recent.id) is not None
