"""FastAPI application factory."""

import asyncio
import contextlib
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from fastapi import FastAPI, Request, Response
from sqlalchemy.engine import make_url

from app import __version__
from app.api.router import router
from app.core.config import Settings, get_settings
from app.core.db import get_session_factory
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging
from app.core.request_id import REQUEST_ID_HEADER, clear_request_id, set_request_id
from app.repositories import audit_log_repo
from app.services import embedding_backfill, metadata_suggestion
from app.services.embedding_client import EmbeddingClient, build_embedding_client
from app.services.llm import LLMClient, LLMError, build_llm_client

log = logging.getLogger("app.http")
log_suggestion = logging.getLogger("app.metadata_suggestion")
log_audit = logging.getLogger("app.audit_log")
log_embedding = logging.getLogger("app.embedding_backfill")


def _is_test_database(settings: Settings) -> bool:
    """Same convention `tests/conftest.py::_migrated_test_database` enforces — the
    background scan must never run against `company_ai_test` (it would call the real LLM
    from ordinary `make test` runs whenever `TestClient(app)` starts the app)."""
    database = make_url(settings.database_url).database
    return bool(database and database.endswith("_test"))


async def _metadata_suggestion_loop(settings: Settings, llm: LLMClient) -> None:
    """Phase 3.2 background scan (docs/plans/PHASE_3_2_PLAN.md §3): periodically classifies
    `ready` documents with no suggestion yet. Runs in the same process (ADR-001/002 — no
    new container); each tick opens its own session, independent of any request. A
    per-tick failure is logged and never stops the loop."""
    while True:
        await asyncio.sleep(settings.metadata_suggestion_poll_interval_s)
        try:
            with get_session_factory()() as session:
                processed = metadata_suggestion.run_pending_scan(
                    session, llm, settings, limit=settings.metadata_suggestion_batch_size
                )
            if processed:
                log_suggestion.info(
                    "background scan processed documents", extra={"count": processed}
                )
        except LLMError as exc:
            log_suggestion.warning("background scan LLM error", extra={"error": str(exc)})
        except Exception:
            log_suggestion.exception("background scan tick failed")


async def _audit_log_cleanup_loop(settings: Settings) -> None:
    """Phase 3.4 (SPEC_06 §1: 90-day retention, daily cleanup). Interval defaults to 6h —
    comfortably covers "daily", and a `DELETE ... WHERE timestamp < cutoff` is cheap and
    idempotent, so running it more often than strictly needed is harmless. Same
    test-database guard as the other loops; `python -m app.cli cleanup-audit-log` is the
    manual/scriptable equivalent for a host cron, if preferred over this loop."""
    while True:
        await asyncio.sleep(settings.audit_log_cleanup_interval_s)
        try:
            cutoff = datetime.now(UTC) - timedelta(days=settings.audit_log_retention_days)
            with get_session_factory()() as session:
                deleted = audit_log_repo.delete_older_than(session, cutoff)
            if deleted:
                log_audit.info("audit log cleanup", extra={"deleted": deleted})
        except Exception:
            log_audit.exception("audit log cleanup tick failed")


async def _embedding_backfill_loop(settings: Settings, client: EmbeddingClient) -> None:
    """Phase 3.4: populates `document_chunks.embedding` for chunks with none yet, in
    batches, only while `EMBEDDINGS_ENABLED=true` (the caller only starts this task in
    that case). A failed batch is logged and retried next tick — never stops the loop."""
    while True:
        await asyncio.sleep(settings.embedding_backfill_interval_s)
        try:
            with get_session_factory()() as session:
                processed = embedding_backfill.run_pending_scan(
                    session, client, limit=settings.embedding_backfill_batch_size
                )
            if processed:
                log_embedding.info(
                    "embedding backfill processed chunks", extra={"count": processed}
                )
        except Exception:
            log_embedding.exception("embedding backfill tick failed")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    for directory in (settings.documents_dir, settings.excel_dir, settings.app_state_dir):
        directory.mkdir(parents=True, exist_ok=True)
    log.info("startup", extra={"version": __version__, "env": settings.app_env})

    tasks: list[asyncio.Task[None]] = []
    if not _is_test_database(settings):
        try:
            llm = build_llm_client(settings)
        except LLMError:
            log_suggestion.info("metadata suggestion background scan disabled: LLM not configured")
        else:
            tasks.append(asyncio.create_task(_metadata_suggestion_loop(settings, llm)))

        tasks.append(asyncio.create_task(_audit_log_cleanup_loop(settings)))

        if settings.embeddings_enabled:
            embedding_client = build_embedding_client(settings)
            tasks.append(asyncio.create_task(_embedding_backfill_loop(settings, embedding_client)))

    yield

    for task in tasks:
        task.cancel()
    for task in tasks:
        with contextlib.suppress(asyncio.CancelledError):
            await task
    log.info("shutdown")


async def request_context(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    rid = set_request_id(request.headers.get(REQUEST_ID_HEADER))
    started = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        duration_ms = round((time.perf_counter() - started) * 1000, 1)
    response.headers[REQUEST_ID_HEADER] = rid
    log.info(
        "request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    clear_request_id()
    return response


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        lifespan=lifespan,
        docs_url="/api/docs" if settings.app_env == "dev" else None,
        redoc_url=None,
    )
    app.middleware("http")(request_context)
    register_exception_handlers(app)
    app.include_router(router)
    return app


app = create_app()
