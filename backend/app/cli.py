"""Operational commands: `python -m app.cli <command>`."""

import argparse
import logging
import sys
import time

from app.core.config import get_settings
from app.core.db import database_reachable, get_engine, get_session_factory
from app.core.logging import setup_logging
from app.services.admin_seed import ensure_admin_user

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


def cmd_print_answer_prompt() -> int:
    """Print the `/api/ask` system prompt (source of truth) so `make prompt-doc` can mirror
    it into docs/prompts/ANSWER_SYSTEM_PROMPT.md and `make lint` can diff the two."""
    from app.services.answer_prompt import SYSTEM_PROMPT

    print(SYSTEM_PROMPT)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    wait = sub.add_parser("wait-for-db", help="block until Postgres answers SELECT 1")
    wait.add_argument("--timeout", type=int, default=60)
    sub.add_parser("seed-admin", help="create the admin user if it does not exist")
    sub.add_parser(
        "assert-pipeline-schema", help="fail if the Phase 0.2 pipeline tables are missing"
    )
    sub.add_parser("print-answer-prompt", help="print the /api/ask system prompt")
    args = parser.parse_args(argv)

    setup_logging(get_settings().log_level)
    if args.command == "wait-for-db":
        return cmd_wait_for_db(args.timeout)
    if args.command == "seed-admin":
        return cmd_seed_admin()
    if args.command == "assert-pipeline-schema":
        return cmd_assert_pipeline_schema()
    if args.command == "print-answer-prompt":
        return cmd_print_answer_prompt()
    return 2


if __name__ == "__main__":
    sys.exit(main())
