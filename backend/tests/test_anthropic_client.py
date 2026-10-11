"""`AnthropicClient` against a mock HTTP transport — no network, no key (İş Emri
2026-10-11-C)."""

from __future__ import annotations

import logging
from typing import Any

import httpx2
import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.services.llm import (
    LLMAuthError,
    LLMNotConfiguredError,
    LLMRateLimitError,
    LLMRequest,
    LLMResponseError,
    LLMTimeoutError,
    LLMUnavailableError,
    build_llm_client,
)
from app.services.llm.anthropic_client import AnthropicClient, _safe_error_summary

REQUEST = LLMRequest(system="sistem", user="soru", model="claude-haiku-5-5", max_output_tokens=64)


def _message(text: str | None, usage: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "id": "msg_x",
        "type": "message",
        "role": "assistant",
        "model": "claude-haiku-5-5",
        "stop_reason": "end_turn",
        "content": [{"type": "text", "text": text}] if text is not None else [],
        "usage": usage or {"input_tokens": 10, "output_tokens": 5},
    }


def _client(handler: Any) -> AnthropicClient:
    return AnthropicClient(
        api_key="test-key",
        timeout_s=5,
        max_retries=0,
        http_client=httpx2.Client(transport=httpx2.MockTransport(handler)),
    )


def test_request_shape_and_usage_parsed(caplog: pytest.LogCaptureFixture) -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        import json

        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        seen["auth"] = request.headers.get("x-api-key")
        return httpx2.Response(200, json=_message("Merhaba [K1]."))

    with caplog.at_level(logging.INFO, logger="app.services.llm"):
        response = _client(handler).complete(REQUEST)

    assert seen["url"] == "https://api.anthropic.com/v1/messages"
    assert seen["auth"] == "test-key"
    body = seen["body"]
    assert body["model"] == "claude-haiku-5-5"
    assert body["system"] == "sistem"
    assert body["messages"] == [{"role": "user", "content": "soru"}]
    assert body["max_tokens"] == 64
    assert "temperature" not in body  # SDK bu sürümde desteklemiyor (bkz. anthropic_client.py)

    assert response.text == "Merhaba [K1]."
    assert response.model == "claude-haiku-5-5"
    assert (response.tokens_in, response.tokens_out, response.tokens_reasoning) == (10, 5, None)
    assert response.finish_reason == "end_turn"

    record = next(r for r in caplog.records if r.getMessage() == "llm call")
    assert record.tokens_in == 10  # type: ignore[attr-defined]
    assert record.tokens_out == 5  # type: ignore[attr-defined]


def test_json_object_appends_instruction_and_strips_fence() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        import json

        seen["body"] = json.loads(request.content)
        return httpx2.Response(200, json=_message('```json\n{"a": 1}\n```'))

    req = LLMRequest(
        system="sistem",
        user="soru",
        model="claude-haiku-5-5",
        max_output_tokens=64,
        response_format="json_object",
    )
    response = _client(handler).complete(req)

    assert "single valid JSON object" in seen["body"]["system"]
    assert response.text == '{"a": 1}'


@pytest.mark.parametrize(
    ("status", "error"),
    [
        (401, LLMAuthError),
        (403, LLMAuthError),
        (429, LLMRateLimitError),
        (500, LLMUnavailableError),
        (529, LLMUnavailableError),
    ],
)
def test_http_errors_map_to_llm_errors(status: int, error: type[Exception]) -> None:
    def handler(_: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            status, json={"type": "error", "error": {"type": "nope", "message": "nope"}}
        )

    with pytest.raises(error):
        _client(handler).complete(REQUEST)


def test_timeout_maps_to_llm_timeout() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ReadTimeout("slow", request=request)

    with pytest.raises(LLMTimeoutError):
        _client(handler).complete(REQUEST)


def test_connection_failure_maps_to_unavailable() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("refused", request=request)

    with pytest.raises(LLMUnavailableError):
        _client(handler).complete(REQUEST)


def test_empty_completion_is_response_error() -> None:
    def handler(_: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json=_message(""))

    with pytest.raises(LLMResponseError):
        _client(handler).complete(REQUEST)


def test_factory_builds_anthropic_client(settings: Settings) -> None:
    client = build_llm_client(
        settings.model_copy(
            update={"llm_provider": "anthropic", "anthropic_api_key": SecretStr("k")}
        )
    )
    assert isinstance(client, AnthropicClient)


def test_factory_anthropic_without_key_is_not_configured(settings: Settings) -> None:
    with pytest.raises(LLMNotConfiguredError):
        build_llm_client(
            settings.model_copy(update={"llm_provider": "anthropic", "anthropic_api_key": None})
        )
    with pytest.raises(LLMNotConfiguredError):
        build_llm_client(
            settings.model_copy(
                update={"llm_provider": "anthropic", "anthropic_api_key": SecretStr("")}
            )
        )


def test_anthropic_key_env_alias_is_prose_anthropic_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """İş Emri 2026-10-11-C: `ANTHROPIC_API_KEY` adı HİÇ okunmaz — yalnız
    `PROSE_ANTHROPIC_API_KEY` (seed_data/generator ile paylaşılan anahtar). Diğer zorunlu
    ayarlar (DATABASE_URL vb.) gerçek test ortamından (`make test`'in kendi env'i) gelir —
    burada yalnız Anthropic anahtarının kaynağı test ediliyor."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "wrong-key-must-not-be-read")
    monkeypatch.setenv("PROSE_ANTHROPIC_API_KEY", "right-key")
    fresh = Settings()
    assert fresh.anthropic_api_key is not None
    assert fresh.anthropic_api_key.get_secret_value() == "right-key"


def test_rate_limit_logs_safe_error_body_without_key(caplog: pytest.LogCaptureFixture) -> None:
    def handler(_: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            429,
            json={
                "type": "error",
                "error": {"type": "rate_limit_error", "message": "Number of requests exceeded"},
            },
        )

    with (
        caplog.at_level(logging.WARNING, logger="app.services.llm"),
        pytest.raises(LLMRateLimitError),
    ):
        _client(handler).complete(REQUEST)

    record = next(r for r in caplog.records if r.getMessage() == "llm rate limited (429)")
    assert "rate_limit_error" in record.error_body  # type: ignore[attr-defined]
    for r in caplog.records:
        assert "test-key" not in r.getMessage()
        assert "test-key" not in str(getattr(r, "error_body", ""))


def test_529_logs_safe_error_body_without_key(caplog: pytest.LogCaptureFixture) -> None:
    def handler(_: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            529, json={"type": "error", "error": {"type": "overloaded_error", "message": "busy"}}
        )

    with (
        caplog.at_level(logging.WARNING, logger="app.services.llm"),
        pytest.raises(LLMUnavailableError),
    ):
        _client(handler).complete(REQUEST)

    record = next(r for r in caplog.records if r.getMessage() == "llm unavailable (529)")
    assert "overloaded_error" in record.error_body  # type: ignore[attr-defined]
    for r in caplog.records:
        assert "test-key" not in r.getMessage()
        assert "test-key" not in str(getattr(r, "error_body", ""))


def test_safe_error_summary_ignores_unknown_fields() -> None:
    class _FakeExc:
        body = {"error": {"type": "rate_limit_error", "secret_header": "SECRET"}}

    summary = _safe_error_summary(_FakeExc())  # type: ignore[arg-type]
    assert "SECRET" not in summary
    assert "rate_limit_error" in summary


def test_safe_error_summary_handles_missing_body() -> None:
    class _FakeExc:
        body = None

    assert _safe_error_summary(_FakeExc()) == "gövde yok/okunamadı"  # type: ignore[arg-type]
