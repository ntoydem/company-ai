"""`alembic upgrade head` on an empty database, and back."""

import pytest
from alembic import command
from alembic.runtime.migration import MigrationContext
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

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
    assert _current_revision() == "0009"
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
    assert "document_metadata_suggestions" in tables
    assert "audit_log" in tables
    document_columns = {c["name"] for c in inspect(engine).get_columns("documents")}
    assert "external_ref" in document_columns
    assert "ai_suggestion_id" in document_columns
    suggestion_columns = {
        c["name"] for c in inspect(engine).get_columns("document_metadata_suggestions")
    }
    assert {"document_id", "model", "status", "fields", "error"} <= suggestion_columns
    audit_columns = {c["name"] for c in inspect(engine).get_columns("audit_log")}
    assert "chunks_retrieved" in audit_columns
    document_columns = {c["name"] for c in inspect(engine).get_columns("documents")}
    assert "has_macros" in document_columns
    assert "file_name" in document_columns
    assert {
        "user_id",
        "timestamp",
        "question",
        "query_type",
        "documents_retrieved",
        "sources",
        "cost_estimate",
        "execution_ms",
        "request_id",
        "error",
    } <= audit_columns

    assert {"product_level", "warnings"} <= audit_columns
    assert "company_settings" in tables

    with engine.connect() as conn:
        has_vector = conn.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        ).scalar()
        # Migration 0009 inserts the one settings row (demo default: every layer open)
        # and the table refuses a second one.
        rows = conn.execute(text("SELECT id, enabled_products FROM company_settings")).all()
        with pytest.raises(IntegrityError):
            conn.execute(text("INSERT INTO company_settings (id) VALUES (2)"))
    assert has_vector == 1
    assert rows == [(1, ["P1", "P2", "P3"])]


def test_upgrade_head_is_idempotent() -> None:
    command.upgrade(alembic_config(), "head")
    assert _current_revision() == "0009"
