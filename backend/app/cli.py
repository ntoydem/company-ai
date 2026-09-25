"""Operational commands: `python -m app.cli <command>`."""

import argparse
import logging
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.core.config import get_settings
from app.core.db import database_reachable, get_engine, get_session_factory
from app.core.logging import setup_logging
from app.repositories import audit_log_repo
from app.services import embedding_backfill
from app.services.admin_seed import ensure_admin_user
from app.services.demo_departments_seed import (
    ensure_demo_department_memberships,
    ensure_demo_departments,
)
from app.services.demo_documents_seed import ensure_demo_documents
from app.services.demo_projects_seed import ensure_demo_projects
from app.services.demo_users_seed import ensure_demo_users

DEFAULT_MANIFEST = Path("seed_data/documents/manifest.json")

log = logging.getLogger("app.cli")


def cmd_wait_for_db(timeout: int) -> int:
    engine = get_engine()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if database_reachable(engine):
            log.info("database reachable")
            return 0
        time.sleep(1)
    log.error("database not reachable", extra={"timeout_s": timeout})
    return 1


def cmd_seed_admin() -> int:
    with get_session_factory()() as session:
        result = ensure_admin_user(session, get_settings())
    log.info("seed-admin done", extra={"username": result.username, "was_created": result.created})
    return 0


def cmd_seed_demo_users() -> int:
    with get_session_factory()() as session:
        results = ensure_demo_users(session, get_settings())
    log.info(
        "seed-demo-users done",
        extra={
            "usernames": [r.username for r in results],
            "was_created": [r.created for r in results],
        },
    )
    return 0


def cmd_seed_demo_departments() -> int:
    with get_session_factory()() as session:
        settings = get_settings()
        departments = ensure_demo_departments(session, settings)
        memberships = ensure_demo_department_memberships(session, settings)
    log.info(
        "seed-demo-departments done",
        extra={
            "slugs": [r.slug for r in departments],
            "memberships": [r.slug for r in memberships],
        },
    )
    return 0


def cmd_seed_demo_projects() -> int:
    with get_session_factory()() as session:
        results = ensure_demo_projects(session, get_settings())
    log.info(
        "seed-demo-projects done",
        extra={"codes": [r.code for r in results], "was_created": [r.created for r in results]},
    )
    return 0


def cmd_seed_demo_documents(manifest: Path) -> int:
    with get_session_factory()() as session:
        results = ensure_demo_documents(session, get_settings(), manifest)
    log.info(
        "seed-demo-documents done",
        extra={
            "refs": [r.external_ref for r in results],
            "was_created": [r.created for r in results],
        },
    )
    return 0


def cmd_wait_for_documents(timeout: int) -> int:
    from sqlalchemy import select

    from app.models.document import Document

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with get_session_factory()() as session:
            rows = session.scalars(select(Document).where(Document.external_ref.is_not(None))).all()
            failed = [row.external_ref for row in rows if row.ingestion_status.value == "failed"]
            if failed:
                log.error("document ingestion failed", extra={"refs": failed})
                return 1
            if rows and all(row.ingestion_status.value == "ready" for row in rows):
                log.info("wait-for-documents: all ready", extra={"count": len(rows)})
                return 0
        time.sleep(2)
    log.error("wait-for-documents: timeout", extra={"timeout_s": timeout})
    return 1


def cmd_assert_pipeline_schema() -> int:
    """Fail if the Phase 0.2 pipeline tables are missing.

    Used by `make test` between the backend and ocr-worker pytest runs, to prove
    ocr-worker's tests only ever execute after the backend's Alembic migration has
    actually been applied to the test database (not just assumed from run order).
    """
    from sqlalchemy import inspect

    required = {"documents", "document_pages", "document_chunks", "ingestion_jobs"}
    tables = set(inspect(get_engine()).get_table_names())
    missing = required - tables
    if missing:
        log.error("pipeline schema missing", extra={"missing_tables": sorted(missing)})
        return 1
    log.info("pipeline schema present", extra={"tables": sorted(required)})
    return 0


def cmd_print_excel_prompts() -> int:
    """Print the two Excel prompts (planning + phrasing, Phase 4.2) so `make prompt-doc`
    can mirror them into docs/prompts/EXCEL_PROMPTS.md and `make lint` can diff."""
    from app.services.excel_ask import ANSWER_SYSTEM_PROMPT, PLAN_SYSTEM_PROMPT

    print("=== PLAN (LLM_MODEL_CLASSIFY, json_object) ===")
    print(PLAN_SYSTEM_PROMPT)
    print("=== ANSWER (LLM_MODEL_ANSWER) ===")
    print(ANSWER_SYSTEM_PROMPT)
    return 0


def cmd_print_answer_prompt() -> int:
    """Print the `/api/ask` system prompt (source of truth) so `make prompt-doc` can mirror
    it into docs/prompts/ANSWER_SYSTEM_PROMPT.md and `make lint` can diff the two."""
    from app.services.answer_prompt import SYSTEM_PROMPT

    print(SYSTEM_PROMPT)
    return 0


def cmd_cleanup_audit_log() -> int:
    """Manual/scriptable equivalent of the background cleanup loop (SPEC_06 §1: 90-day
    retention) — for a host cron, or a one-off run outside the normal 6h interval."""
    settings = get_settings()
    cutoff = datetime.now(UTC) - timedelta(days=settings.audit_log_retention_days)
    with get_session_factory()() as session:
        deleted = audit_log_repo.delete_older_than(session, cutoff)
    log.info("cleanup-audit-log done", extra={"deleted": deleted, "cutoff": cutoff.isoformat()})
    return 0


def cmd_backfill_embeddings(limit: int) -> int:
    """One backfill batch (Phase 3.4). No-op if `EMBEDDINGS_ENABLED=false` — never calls
    a possibly-absent `embed` service just because someone ran this command."""
    settings = get_settings()
    if not settings.embeddings_enabled:
        log.info("backfill-embeddings: EMBEDDINGS_ENABLED=false, nothing to do")
        return 0
    from app.services.embedding_client import build_embedding_client

    client = build_embedding_client(settings)
    with get_session_factory()() as session:
        processed = embedding_backfill.run_pending_scan(session, client, limit=limit)
    log.info("backfill-embeddings done", extra={"processed": processed})
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    wait = sub.add_parser("wait-for-db", help="block until Postgres answers SELECT 1")
    wait.add_argument("--timeout", type=int, default=60)
    sub.add_parser("seed-admin", help="create the admin user if it does not exist")
    sub.add_parser("seed-demo-users", help="create the demo users if they do not exist")
    sub.add_parser(
        "seed-demo-departments",
        help="create the demo departments and demo user memberships if they do not exist",
    )
    sub.add_parser("seed-demo-projects", help="create the demo projects if they do not exist")
    seed_docs = sub.add_parser(
        "seed-demo-documents",
        help="create the demo documents from seed_data/documents/manifest.json",
    )
    seed_docs.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    wait_docs = sub.add_parser(
        "wait-for-documents", help="block until every seeded document is ready or one fails"
    )
    wait_docs.add_argument("--timeout", type=int, default=600)
    sub.add_parser(
        "assert-pipeline-schema", help="fail if the Phase 0.2 pipeline tables are missing"
    )
    sub.add_parser("print-answer-prompt", help="print the /api/ask system prompt")
    sub.add_parser("print-excel-prompts", help="print the /api/excel/ask plan + answer prompts")
    sub.add_parser(
        "cleanup-audit-log", help="delete audit_log rows older than AUDIT_LOG_RETENTION_DAYS"
    )
    backfill = sub.add_parser(
        "backfill-embeddings", help="embed one batch of document_chunks with no vector yet"
    )
    backfill.add_argument("--limit", type=int, default=20)
    args = parser.parse_args(argv)

    setup_logging(get_settings().log_level)
    if args.command == "wait-for-db":
        return cmd_wait_for_db(args.timeout)
    if args.command == "seed-admin":
        return cmd_seed_admin()
    if args.command == "seed-demo-users":
        return cmd_seed_demo_users()
    if args.command == "seed-demo-departments":
        return cmd_seed_demo_departments()
    if args.command == "seed-demo-projects":
        return cmd_seed_demo_projects()
    if args.command == "seed-demo-documents":
        return cmd_seed_demo_documents(args.manifest)
    if args.command == "wait-for-documents":
        return cmd_wait_for_documents(args.timeout)
    if args.command == "assert-pipeline-schema":
        return cmd_assert_pipeline_schema()
    if args.command == "print-answer-prompt":
        return cmd_print_answer_prompt()
    if args.command == "print-excel-prompts":
        return cmd_print_excel_prompts()
    if args.command == "cleanup-audit-log":
        return cmd_cleanup_audit_log()
    if args.command == "backfill-embeddings":
        return cmd_backfill_embeddings(args.limit)
    return 2


if __name__ == "__main__":
    sys.exit(main())
