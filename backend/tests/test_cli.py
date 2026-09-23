"""`assert-pipeline-schema` — the check `make test` runs between the backend and
ocr-worker pytest passes to prove the Phase 0.2 migration actually landed first."""

import pytest

from app import cli


def test_seed_demo_users_succeeds_and_is_idempotent() -> None:
    """Exercises the real `log.info(..., extra={...})` call end-to-end — a reserved
    `LogRecord` attribute name in `extra` (e.g. `created`) raises `KeyError` at log time,
    which a test only calling `ensure_demo_users` directly would never catch."""
    assert cli.cmd_seed_demo_users() == 0
    assert cli.cmd_seed_demo_users() == 0


def test_assert_pipeline_schema_succeeds_once_migrated() -> None:
    # The session-scoped `_migrated_test_database` fixture has already run `alembic
    # upgrade head` by the time any test executes, so the pipeline tables exist here.
    assert cli.cmd_assert_pipeline_schema() == 0


def test_assert_pipeline_schema_fails_when_a_table_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import sqlalchemy

    class _FakeInspector:
        def get_table_names(self) -> list[str]:
            return ["users", "documents"]  # document_pages/chunks/ingestion_jobs missing

    # `cmd_assert_pipeline_schema` imports `inspect` locally at call time, so patching
    # the `sqlalchemy` module's attribute here is picked up by that fresh import.
    monkeypatch.setattr(sqlalchemy, "inspect", lambda _engine: _FakeInspector())
    assert cli.cmd_assert_pipeline_schema() == 1
