"""Admin project CRUD (SPEC_02 §6) — Phase 1.2 kabul kriteri 3."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from tests.department_fixtures import make_department


def test_admin_can_create_and_update_project(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    finans = make_department(db_session, slug="finans")

    create_response = client.post(
        "/api/projects",
        json={
            "name": "Ankara RES",
            "code": "ANK_RES",
            "stage": "operation",
            "department_ids": [str(finans.id)],
        },
    )
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["code"] == "ANK_RES"
    assert body["stage"] == "operation"
    assert body["department_ids"] == [str(finans.id)]

    update_response = client.patch(f"/api/projects/{body['id']}", json={"is_active": False})
    assert update_response.status_code == 200
    assert update_response.json()["is_active"] is False


def test_employee_create_project_returns_403(client: TestClient, employee_user: User) -> None:
    response = client.post("/api/projects", json={"name": "X", "code": "X_PRJ"})
    assert response.status_code == 403


def test_duplicate_project_code_returns_409(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    assert client.post("/api/projects", json={"name": "A", "code": "DUP"}).status_code == 201
    response = client.post("/api/projects", json={"name": "B", "code": "DUP"})
    assert response.status_code == 409


def test_create_project_with_unknown_department_id_returns_404(
    client: TestClient, admin_user: User
) -> None:
    response = client.post(
        "/api/projects",
        json={"name": "X", "code": "X2", "department_ids": [str(uuid.uuid4())]},
    )
    assert response.status_code == 404


def test_employee_can_list_projects(client: TestClient, employee_user: User) -> None:
    response = client.get("/api/projects")
    assert response.status_code == 200
