"""`alembic upgrade head` on an empty database, and back."""

from alembic import command
from alembic.runtime.migration import MigrationContext
from sqlalchemy import inspect, text

from app.core.db import get_engine
from tests.conftest import alembic_config


def _current_revision() -> str | None:
    with get_engine().connect() as conn:
        return MigrationContext.configure(conn).get_current_revision()


def test_downgrade_to_empty_then_upgrade_head() -> None:
    cfg = alembic_config()
    engine = get_engine()

    command.downgrade(cfg, "base")
    assert _current_revision() is None
    assert "users" not in inspect(engine).get_table_names()

    command.upgrade(cfg, "head")
    assert _current_revision() == "0004"
    tables = inspect(engine).get_table_names()
    assert "users" in tables
    assert "documents" in tables
    assert "document_pages" in tables
    assert "document_chunks" in tables
    assert "ingestion_jobs" in tables
    assert "departments" in tables
    assert "user_departments" in tables
    assert "projects" in tables
    assert "project_departments" in tables
    document_columns = {c["name"] for c in inspect(engine).get_columns("documents")}
    assert "external_ref" in document_columns

    with engine.connect() as conn:
        has_vector = conn.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        ).scalar()
    assert has_vector == 1


def test_upgrade_head_is_idempotent() -> None:
    command.upgrade(alembic_config(), "head")
    assert _current_revision() == "0004"
