"""Admin user management (Phase 5.2, SPEC_06 §2)."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.users import PRIMARY_DEPARTMENT_NOT_A_MEMBERSHIP_MESSAGE
from app.core.config import Settings
from app.models.user import User
from app.services.admin_seed import ensure_admin_user
from tests.department_fixtures import make_department


def test_admin_can_create_and_list_users(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    finans = make_department(db_session, slug="finans")

    create_response = client.post(
        "/api/users",
        json={
            "username": "yeni-calisan",
            "password": "gecerli-sifre",
            "display_name": "Yeni Çalışan",
            "role": "employee",
            "department_ids": [str(finans.id)],
        },
    )
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["username"] == "yeni-calisan"
    assert body["role"] == "employee"
    assert body["department_ids"] == [str(finans.id)]
    assert body["department_slugs"] == ["finans"]
    assert "password" not in body
    assert "password_hash" not in body

    list_response = client.get("/api/users")
    assert list_response.status_code == 200
    usernames = [u["username"] for u in list_response.json()]
    assert "yeni-calisan" in usernames
    assert admin_user.username in usernames


def test_employee_create_user_returns_403(client: TestClient, employee_user: User) -> None:
    response = client.post(
        "/api/users",
        json={"username": "x", "password": "gecerli-sifre", "display_name": "X"},
    )
    assert response.status_code == 403


def test_employee_list_users_returns_403(client: TestClient, employee_user: User) -> None:
    assert client.get("/api/users").status_code == 403


def test_create_user_duplicate_username_returns_409(client: TestClient, admin_user: User) -> None:
    body = {"username": "dup", "password": "gecerli-sifre", "display_name": "Dup"}
    assert client.post("/api/users", json=body).status_code == 201
    response = client.post("/api/users", json=body)
    assert response.status_code == 409


def test_create_user_unknown_department_id_returns_404(
    client: TestClient, admin_user: User
) -> None:
    response = client.post(
        "/api/users",
        json={
            "username": "x2",
            "password": "gecerli-sifre",
            "display_name": "X2",
            "department_ids": [str(uuid.uuid4())],
        },
    )
    assert response.status_code == 404


def test_admin_can_update_role_and_department_membership(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    finans = make_department(db_session, slug="finans")
    create_response = client.post(
        "/api/users",
        json={"username": "terfi", "password": "gecerli-sifre", "display_name": "Terfi"},
    )
    user_id = create_response.json()["id"]

    response = client.patch(
        f"/api/users/{user_id}",
        json={"role": "management", "is_active": False, "department_ids": [str(finans.id)]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "management"
    assert body["is_active"] is False
    assert body["department_ids"] == [str(finans.id)]


def test_admin_cannot_demote_self(client: TestClient, admin_user: User) -> None:
    response = client.patch(f"/api/users/{admin_user.id}", json={"role": "employee"})
    assert response.status_code == 409


def test_admin_cannot_disable_self(client: TestClient, admin_user: User) -> None:
    response = client.patch(f"/api/users/{admin_user.id}", json={"is_active": False})
    assert response.status_code == 409


def test_admin_can_edit_own_display_name(client: TestClient, admin_user: User) -> None:
    """T6's lockout guard is scoped to role/is_active only — other self-edits are fine."""
    response = client.patch(f"/api/users/{admin_user.id}", json={"display_name": "Yeni Ad"})
    assert response.status_code == 200
    assert response.json()["display_name"] == "Yeni Ad"


def test_update_unknown_user_returns_404(client: TestClient, admin_user: User) -> None:
    response = client.patch(f"/api/users/{uuid.uuid4()}", json={"display_name": "x"})
    assert response.status_code == 404


def test_department_assignment_via_admin_api_reflects_in_own_me(
    client: TestClient, db_session: Session, settings: Settings
) -> None:
    """End-to-end: no `admin_user`/`get_current_user` override here — the admin creates
    the user and assigns a department through the real login flow, then the new user logs
    in themself and sees the membership on `/api/auth/me` (same field `test_me_returns_
    direct_department_memberships` in test_auth.py checks via a direct DB write)."""
    ensure_admin_user(db_session, settings)
    finans = make_department(db_session, slug="finans")
    admin_login = client.post(
        "/api/auth/login",
        json={
            "username": settings.admin_username,
            "password": settings.admin_password.get_secret_value(),
        },
    )
    assert admin_login.status_code == 200

    create_response = client.post(
        "/api/users",
        json={
            "username": "finans-calisani",
            "password": "gecerli-sifre",
            "display_name": "Finans Çalışanı",
            "department_ids": [str(finans.id)],
        },
    )
    assert create_response.status_code == 201
    client.post("/api/auth/logout")

    user_login = client.post(
        "/api/auth/login", json={"username": "finans-calisani", "password": "gecerli-sifre"}
    )
    assert user_login.status_code == 200

    me_response = client.get("/api/auth/me")

    assert me_response.json()["department_slugs"] == ["finans"]


def test_update_user_unknown_department_id_returns_404(
    client: TestClient, admin_user: User
) -> None:
    create_response = client.post(
        "/api/users",
        json={"username": "x3", "password": "gecerli-sifre", "display_name": "X3"},
    )
    user_id = create_response.json()["id"]

    response = client.patch(f"/api/users/{user_id}", json={"department_ids": [str(uuid.uuid4())]})

    assert response.status_code == 404


# --- Aşama C: B-09 primary department rule + B-05 title through the admin API ---


def test_create_user_defaults_primary_to_first_membership_and_stores_title(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    hukuk = make_department(db_session, slug="hukuk")
    finans = make_department(db_session, slug="finans")
    body = client.post(
        "/api/users",
        json={
            "username": "iki-departman",
            "password": "gecerli-sifre",
            "display_name": "İki Departman",
            "department_ids": [str(hukuk.id), str(finans.id)],
            "title": "Uzman",
        },
    ).json()
    assert body["primary_department_id"] == str(finans.id)  # first by slug
    assert body["department_slugs"] == ["finans", "hukuk"]
    assert body["title"] == "Uzman"


def test_primary_department_must_be_a_membership(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    hukuk = make_department(db_session, slug="hukuk")
    finans = make_department(db_session, slug="finans")
    response = client.post(
        "/api/users",
        json={
            "username": "yanlis-ana",
            "password": "gecerli-sifre",
            "display_name": "Yanlış Ana",
            "department_ids": [str(hukuk.id)],
            "primary_department_id": str(finans.id),
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"] == PRIMARY_DEPARTMENT_NOT_A_MEMBERSHIP_MESSAGE


def test_update_keeps_primary_while_member_and_moves_it_when_dropped(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    hukuk = make_department(db_session, slug="hukuk")
    finans = make_department(db_session, slug="finans")
    created = client.post(
        "/api/users",
        json={
            "username": "tasinan",
            "password": "gecerli-sifre",
            "display_name": "Taşınan",
            "department_ids": [str(hukuk.id), str(finans.id)],
            "primary_department_id": str(hukuk.id),
        },
    ).json()
    user_id = created["id"]
    assert created["primary_department_id"] == str(hukuk.id)

    # Adding a membership without naming a primary keeps the current one.
    body = client.patch(
        f"/api/users/{user_id}", json={"department_ids": [str(hukuk.id), str(finans.id)]}
    ).json()
    assert body["primary_department_id"] == str(hukuk.id)
    # Dropping the primary's membership moves the primary to the first remaining one.
    body = client.patch(f"/api/users/{user_id}", json={"department_ids": [str(finans.id)]}).json()
    assert body["primary_department_id"] == str(finans.id)
    # Explicitly naming a non-member is rejected.
    assert (
        client.patch(
            f"/api/users/{user_id}", json={"primary_department_id": str(hukuk.id)}
        ).status_code
        == 422
    )
    # No memberships at all → no primary.
    body = client.patch(f"/api/users/{user_id}", json={"department_ids": []}).json()
    assert body["primary_department_id"] is None and body["department_slugs"] == []
