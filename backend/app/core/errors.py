"""Error responses: Turkish, no technical detail for the user; full detail in the JSON log."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.request_id import REQUEST_ID_HEADER, get_request_id

log = logging.getLogger(__name__)

GENERIC_ERROR_MESSAGE = "Beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin."
VALIDATION_ERROR_MESSAGE = "İstek geçersiz."


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


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.exception(
        "unhandled exception",
        extra={"path": request.url.path, "method": request.method, "error": repr(exc)},
    )
    return _response(500, GENERIC_ERROR_MESSAGE)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
