import json
import logging

from app.core.logging import MASK, JsonFormatter
from app.core.request_id import clear_request_id, set_request_id


def _record(msg: str, extra: dict[str, object] | None = None) -> logging.LogRecord:
    record = logging.LogRecord("app.test", logging.INFO, __file__, 1, msg, (), None)
    for key, value in (extra or {}).items():
        setattr(record, key, value)
    return record


def test_log_line_is_json_with_request_id() -> None:
    set_request_id("req-log-1")
    try:
        line = JsonFormatter().format(_record("hello", {"user": "admin"}))
    finally:
        clear_request_id()
    payload = json.loads(line)
    assert payload["message"] == "hello"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.test"
    assert payload["request_id"] == "req-log-1"
    assert payload["user"] == "admin"
    assert payload["ts"].endswith("+00:00")


def test_sensitive_extra_fields_are_masked() -> None:
    line = JsonFormatter().format(
        _record("login", {"password": "hunter2", "api_key": "AIza-fake", "llm_token": "t"})
    )
    payload = json.loads(line)
    assert payload["password"] == MASK
    assert payload["api_key"] == MASK
    assert payload["llm_token"] == MASK
    assert "hunter2" not in line
    assert "AIza-fake" not in line


def test_exception_is_included_in_log_not_in_message() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        record = logging.LogRecord("app.test", logging.ERROR, __file__, 1, "failed", (), None)
        import sys

        record.exc_info = sys.exc_info()
    payload = json.loads(JsonFormatter().format(record))
    assert "ValueError: boom" in payload["exception"]
    assert payload["message"] == "failed"


def test_token_counters_are_not_masked() -> None:
    """`tokens_in` / `tokens_out` are LLM usage counters (ADR-009), not secrets."""
    line = JsonFormatter().format(_record("llm call", {"tokens_in": 10, "tokens_out": 5}))
    payload = json.loads(line)
    assert payload["tokens_in"] == 10 and payload["tokens_out"] == 5
