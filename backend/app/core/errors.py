"""Error responses: Turkish, no technical detail for the user; full detail in the JSON log."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.request_id import REQUEST_ID_HEADER, get_request_id
from app.services.llm import LLMError, LLMNotConfiguredError

log = logging.getLogger(__name__)

GENERIC_ERROR_MESSAGE = "Beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin."
VALIDATION_ERROR_MESSAGE = "İstek geçersiz."
LLM_UNAVAILABLE_MESSAGE = "Yapay zeka servisi geçici olarak kullanılamıyor."
LLM_NOT_CONFIGURED_MESSAGE = "Yapay zeka servisi yapılandırılmamış."
NOT_AUTHENTICATED_MESSAGE = "Oturum açmanız gerekiyor."
NOT_AUTHORIZED_MESSAGE = "Bu işlem için yetkiniz yok."


def _response(status_code: int, detail: object) -> JSONResponse:
    rid = get_request_id()
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "request_id": rid},
        headers={REQUEST_ID_HEADER: rid} if rid else None,
    )


async def http_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    return _response(exc.status_code, exc.detail)


async def validation_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    return _response(422, {"message": VALIDATION_ERROR_MESSAGE, "errors": exc.errors()})


async def llm_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """LLM failures degrade only `/api/ask` (SPEC_06 §8); detail goes to the log, never to
    the user."""
    assert isinstance(exc, LLMError)
    if isinstance(exc, LLMNotConfiguredError):
        log.warning("llm not configured", extra={"path": request.url.path, "error": str(exc)})
        return _response(503, LLM_NOT_CONFIGURED_MESSAGE)
    log.error(
        "llm call failed",
        extra={"path": request.url.path, "error_type": type(exc).__name__, "error": str(exc)},
    )
    return _response(503, LLM_UNAVAILABLE_MESSAGE)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.exception(
        "unhandled exception",
        extra={"path": request.url.path, "method": request.method, "error": repr(exc)},
    )
    return _response(500, GENERIC_ERROR_MESSAGE)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(LLMError, llm_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
