"""`POST /api/auth/login|logout`, `GET /api/auth/me` — Phase 1.1 kabul kriterleri."""

import logging

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy.orm import Session

from app.api.auth import INVALID_CREDENTIALS_MESSAGE, TOO_MANY_ATTEMPTS_MESSAGE
from app.core.config import Settings
from app.core.errors import NOT_AUTHENTICATED_MESSAGE
from app.core.logging import JsonFormatter
from app.models.user import User
from app.repositories import user_repo
from app.services.admin_seed import ensure_admin_user
from app.services.security import ACCESS_TOKEN_COOKIE_NAME


def _login(client: TestClient, username: str, password: str) -> Response:
    return client.post("/api/auth/login", json={"username": username, "password": password})


def test_login_with_correct_credentials_returns_200_and_sets_cookie(
    client: TestClient, db_session: Session, settings: Settings
) -> None:
    ensure_admin_user(db_session, settings)

    response = _login(client, settings.admin_username, settings.admin_password.get_secret_value())

    assert response.status_code == 200
    assert ACCESS_TOKEN_COOKIE_NAME in response.cookies
    body = response.json()
    assert body["username"] == settings.admin_username
    assert "password_hash" not in body
    assert "password" not in body


def test_login_with_wrong_password_returns_401(
    client: TestClient, db_session: Session, settings: Settings
) -> None:
    ensure_admin_user(db_session, settings)

    response = _login(client, settings.admin_username, "kesinlikle-yanlis-sifre")

    assert response.status_code == 401
    assert response.json()["detail"] == INVALID_CREDENTIALS_MESSAGE
    assert ACCESS_TOKEN_COOKIE_NAME not in response.cookies


def test_login_with_inactive_user_returns_401(client: TestClient, inactive_user: User) -> None:
    response = _login(client, inactive_user.username, "gecerli-sifre")

    assert response.status_code == 401
    assert response.json()["detail"] == INVALID_CREDENTIALS_MESSAGE


def test_login_failure_paths_return_identical_error_body(
    client: TestClient, db_session: Session, settings: Settings, inactive_user: User
) -> None:
    """Wrong password, disabled account and unknown username must be indistinguishable —
    otherwise an attacker could enumerate valid usernames by the error they get back."""
    ensure_admin_user(db_session, settings)

    wrong_password = _login(client, settings.admin_username, "kesinlikle-yanlis-sifre")
    disabled_account = _login(client, inactive_user.username, "gecerli-sifre")
    unknown_username = _login(client, "boyle-bir-kullanici-yok", "her-hangi-bir-sifre")

    # `request_id` legitimately differs per call (request tracing); only `detail` — the
    # part the client actually sees as the reason — must be indistinguishable.
    details = {
        wrong_password.json()["detail"],
        disabled_account.json()["detail"],
        unknown_username.json()["detail"],
    }
    statuses = {
        wrong_password.status_code,
        disabled_account.status_code,
        unknown_username.status_code,
    }
    assert details == {INVALID_CREDENTIALS_MESSAGE}
    assert statuses == {401}


def test_me_without_cookie_returns_401(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == NOT_AUTHENTICATED_MESSAGE


def test_me_with_valid_cookie_returns_current_user(
    client: TestClient, db_session: Session, settings: Settings
) -> None:
    ensure_admin_user(db_session, settings)
    _login(client, settings.admin_username, settings.admin_password.get_secret_value())

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == settings.admin_username
    assert body["role"] == "admin"


def test_logout_clears_cookie_without_requiring_auth(client: TestClient) -> None:
    response = client.post("/api/auth/logout")

    assert response.status_code == 204
    assert ACCESS_TOKEN_COOKIE_NAME not in client.cookies


def test_login_failure_does_not_log_password_or_hash(
    client: TestClient, db_session: Session, settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    ensure_admin_user(db_session, settings)
    admin = user_repo.get_by_username(db_session, settings.admin_username)
    assert admin is not None
    sentinel_password = "SENTINEL-ASLA-LOGLANMAMALI-987"

    with caplog.at_level(logging.INFO, logger="app.api.auth"):
        _login(client, settings.admin_username, sentinel_password)

    formatter = JsonFormatter()
    for record in caplog.records:
        rendered = formatter.format(record)
        assert sentinel_password not in rendered
        assert admin.password_hash not in rendered


def test_login_rate_limited_after_repeated_failures_returns_429(
    client: TestClient, db_session: Session, settings: Settings
) -> None:
    ensure_admin_user(db_session, settings)

    for _ in range(5):
        response = _login(client, settings.admin_username, "yanlis-sifre")
        assert response.status_code == 401

    blocked = _login(client, settings.admin_username, "yanlis-sifre")

    assert blocked.status_code == 429
    assert blocked.json()["detail"] == TOO_MANY_ATTEMPTS_MESSAGE
