"""FastAPI application factory."""

import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response

from app import __version__
from app.api.router import router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging
from app.core.request_id import REQUEST_ID_HEADER, clear_request_id, set_request_id

log = logging.getLogger("app.http")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    for directory in (settings.documents_dir, settings.excel_dir, settings.app_state_dir):
        directory.mkdir(parents=True, exist_ok=True)
    log.info("startup", extra={"version": __version__, "env": settings.app_env})
    yield
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
