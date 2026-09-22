"""Shared fixtures. Tests run only against the separate `company_ai_test` database."""

from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.db import get_engine, get_session_factory
from app.main import app
from app.models import Base
from app.models.user import User
from app.repositories import user_repo
from app.services.admin_seed import ensure_admin_user


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
def _clean_tables() -> Iterator[None]:
    yield
    with get_engine().begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE'))


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
def admin_user(db_session: Session, settings: Settings) -> User:
    """The seeded admin user, created on demand for tests exercising `get_current_user`."""
    ensure_admin_user(db_session, settings)
    user = user_repo.get_by_username(db_session, settings.admin_username)
    assert user is not None
    return user
