"""Structured JSON logging on stdout. Every record carries the current request id."""

import json
import logging
import logging.config
from datetime import UTC, datetime
from typing import Any

from app.core.request_id import get_request_id

# Keys whose values must never reach the logs, whatever the caller passes as `extra`.
SENSITIVE_KEYS = frozenset(
    {"password", "password_hash", "api_key", "token", "secret", "authorization", "cookie"}
)
MASK = "***"

_STANDARD_ATTRS = frozenset(vars(logging.LogRecord("", 0, "", 0, "", (), None)).keys()) | {
    "message",
    "asctime",
    "taskName",
}


def _mask(key: str, value: Any) -> Any:
    return MASK if any(s in key.lower() for s in SENSITIVE_KEYS) else value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
        }
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                payload[key] = _mask(key, value)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_logging(level: str = "INFO") -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"json": {"()": "app.core.logging.JsonFormatter"}},
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {"level": level.upper(), "handlers": ["stdout"]},
            "loggers": {
                "uvicorn": {"level": "INFO", "handlers": ["stdout"], "propagate": False},
                "uvicorn.error": {"level": "INFO", "handlers": ["stdout"], "propagate": False},
                "uvicorn.access": {"level": "WARNING", "handlers": ["stdout"], "propagate": False},
                "sqlalchemy.engine": {"level": "WARNING"},
            },
        }
    )
