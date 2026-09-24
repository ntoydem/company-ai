"""`GET /api/audit-log`, `GET /api/audit-log/{id}` — admin-only (Phase 3.4, SPEC_06 §1)."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories import audit_log_repo


def _row(session: Session, user: User, **overrides: object) -> AuditLog:
    defaults: dict[str, object] = {
        "user_id": user.id,
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


def test_list_requires_admin(client: TestClient, employee_user: User) -> None:
    assert client.get("/api/audit-log").status_code == 403


def test_detail_requires_admin(client: TestClient, employee_user: User) -> None:
    assert client.get(f"/api/audit-log/{uuid.uuid4()}").status_code == 403


def test_admin_lists_rows_without_heavy_fields(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    row = _row(db_session, admin_user)

    response = client.get("/api/audit-log")

    assert response.status_code == 200
    items = response.json()
    assert [i["id"] for i in items] == [str(row.id)]
    assert items[0]["question"] == "Ankara RES'in güncel DSCR'ı nedir?"
    assert "answer" not in items[0]
    assert "sources" not in items[0]


def test_admin_filters_by_department(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    _row(db_session, admin_user, scope_department="finans")
    _row(db_session, admin_user, scope_department="hukuk")

    response = client.get("/api/audit-log", params={"department": "hukuk"})

    assert [i["scope_department"] for i in response.json()] == ["hukuk"]


def test_admin_filters_by_has_error(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    _row(db_session, admin_user, error=None)
    failed = _row(db_session, admin_user, error="LLM rate limited")

    response = client.get("/api/audit-log", params={"has_error": True})

    assert [i["id"] for i in response.json()] == [str(failed.id)]


def test_admin_gets_full_detail(client: TestClient, db_session: Session, admin_user: User) -> None:
    row = _row(db_session, admin_user)

    response = client.get(f"/api/audit-log/{row.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "1,20x [K1]."
    assert body["sources"] == [{"ref": "K1", "title": "Facility Agreement"}]
    assert body["cost_estimate"] is None


def test_detail_unknown_id_returns_404(client: TestClient, admin_user: User) -> None:
    response = client.get(f"/api/audit-log/{uuid.uuid4()}")
    assert response.status_code == 404
