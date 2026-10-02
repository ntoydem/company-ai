"""Shared fixtures. Tests run only against the separate `company_ai_test` database."""

from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.api import deps as deps_module
from app.api.deps import get_current_user, get_llm_client, get_router
from app.core.config import Settings, get_settings
from app.core.db import get_engine, get_session_factory
from app.main import app
from app.models import Base
from app.models.company_settings import SETTINGS_ROW_ID
from app.models.user import User, UserRole
from app.repositories import user_repo
from app.services.admin_seed import ensure_admin_user
from app.services.security import hash_password
from tests.fakes import FakeLLMClient, FakeRouter


def alembic_config() -> Config:
    return Config("alembic.ini")


@pytest.fixture(scope="session", autouse=True)
def _migrated_test_database() -> Iterator[None]:
    url = make_url(get_settings().database_url)
    assert url.database and url.database.endswith("_test"), (
        f"refusing to run tests against non-test database {url.database!r}; "
        "set DATABASE_URL to the *_test database (make test does this)"
    )
    command.upgrade(alembic_config(), "head")
    yield


@pytest.fixture(autouse=True)
def _reset_login_rate_limiter() -> None:
    """The login rate limiter is a process-wide in-memory singleton (ADR-015) — without
    this, failed-login attempts in one test would count towards another test's budget."""
    deps_module._login_rate_limiter.cache_clear()


@pytest.fixture(autouse=True)
def _clean_tables() -> Iterator[None]:
    yield
    with get_engine().begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE'))
        # Migration 0009 inserts the one `company_settings` row; the truncate above removes
        # it, so restore it exactly as the migration does (demo default: every layer open).
        # A test that switched to P1-only therefore never leaks into the next one.
        conn.execute(text(f"INSERT INTO company_settings (id) VALUES ({SETTINGS_ROW_ID})"))


@pytest.fixture
def settings() -> Settings:
    return get_settings()


@pytest.fixture
def db_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def fake_llm() -> Iterator[FakeLLMClient]:
    """Shared by every test hitting an endpoint that depends on `get_llm_client`
    (`/api/ask`, Phase 3.2's `/suggest-metadata`) — no network, records every request."""
    fake = FakeLLMClient()
    app.dependency_overrides[get_llm_client] = lambda: fake
    # Phase 4.3: `/api/ask` is routed first. A DOCUMENT-only fake router keeps every
    # pre-router test seeing exactly the LLM calls it always did; `fake_router` replaces it.
    default_router = FakeRouter()
    app.dependency_overrides[get_router] = lambda: default_router
    try:
        yield fake
    finally:
        app.dependency_overrides.pop(get_llm_client, None)
        app.dependency_overrides.pop(get_router, None)


@pytest.fixture
def fake_router(fake_llm: FakeLLMClient) -> Iterator[FakeRouter]:
    """A router whose `query_type` the test sets (`fake_router.query_type = "MIXED_QUERY"`)."""
    del fake_llm
    router = FakeRouter()
    app.dependency_overrides[get_router] = lambda: router
    try:
        yield router
    finally:
        app.dependency_overrides.pop(get_router, None)


@pytest.fixture
def admin_user(db_session: Session, settings: Settings) -> Iterator[User]:
    """The seeded admin user, authenticated as the current user for the duration of the
    test via a `get_current_user` override (same pattern as `fake_llm`/`get_llm_client`
    in test_ask.py). Tests exercising the real login flow itself use `ensure_admin_user`
    directly instead, so this override can't mask a bug in `/api/auth/login`."""
    ensure_admin_user(db_session, settings)
    user = user_repo.get_by_username(db_session, settings.admin_username)
    assert user is not None
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        yield user
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def employee_user(db_session: Session) -> Iterator[User]:
    """A plain `employee` with no department membership; tests attach departments via
    `tests.department_fixtures.add_user_to_department`. Same override pattern as
    `admin_user`."""
    user = user_repo.create(
        db_session,
        username="test-calisan",
        password_hash=hash_password("gecerli-sifre"),
        display_name="Test Çalışan",
        role=UserRole.employee,
    )
    db_session.commit()
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        yield user
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def management_user(db_session: Session) -> Iterator[User]:
    """A `management` user — sees every department regardless of membership (SPEC_02 §5),
    so no membership rows are needed."""
    user = user_repo.create(
        db_session,
        username="test-yonetim",
        password_hash=hash_password("gecerli-sifre"),
        display_name="Test Yönetim",
        role=UserRole.management,
    )
    db_session.commit()
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        yield user
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def department_manager_user(db_session: Session) -> Iterator[User]:
    """A `department_manager` with no membership yet (B-08); tests attach the department
    they manage via `add_user_to_department` — the role has no department of its own."""
    user = user_repo.create(
        db_session,
        username="test-mudur",
        password_hash=hash_password("gecerli-sifre"),
        display_name="Test Müdür",
        role=UserRole.department_manager,
    )
    db_session.commit()
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        yield user
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def inactive_user(db_session: Session) -> User:
    """A disabled user, created ad hoc so tests never mutate seeded demo-account state."""
    user = user_repo.create(
        db_session,
        username="devre-disi",
        password_hash=hash_password("gecerli-sifre"),
        display_name="Devre Dışı Kullanıcı",
        role=UserRole.employee,
    )
    user.is_active = False
    db_session.commit()
    return user
