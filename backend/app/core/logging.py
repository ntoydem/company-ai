"""Structured JSON logging on stdout. Every record carries the current request id."""

import json
import logging
import logging.config
import re
from datetime import UTC, datetime
from typing import Any

from app.core.request_id import get_request_id

# Keys whose values must never reach the logs, whatever the caller passes as `extra`.
SENSITIVE_KEYS = frozenset(
    {"password", "password_hash", "api_key", "token", "secret", "authorization", "cookie"}
)
MASK = "***"
# "token" is matched as a whole segment (`llm_token`, `access_token`) so that LLM usage
# counters (`tokens_in`, `tokens_out`, ADR-009) stay readable; the other keys match as
# substrings.
_SEGMENT_ONLY_KEYS = frozenset({"token"})

_STANDARD_ATTRS = frozenset(vars(logging.LogRecord("", 0, "", 0, "", (), None)).keys()) | {
    "message",
    "asctime",
    "taskName",
}


def _is_sensitive(key: str) -> bool:
    lowered = key.lower()
    segments = set(re.split(r"[^a-z0-9]+", lowered))
    for sensitive in SENSITIVE_KEYS:
        if sensitive in _SEGMENT_ONLY_KEYS:
            if sensitive in segments:
                return True
        elif sensitive in lowered:
            return True
    return False


def _mask(key: str, value: Any) -> Any:
    return MASK if _is_sensitive(key) else value


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
