"""`OpenAICompatibleClient` against a mock HTTP transport — no network, no key."""

from __future__ import annotations

import json
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
from app.services.llm.openai_compatible import OpenAICompatibleClient, _safe_error_summary

REQUEST = LLMRequest(
    system="sistem", user="soru", model="gemini-test", max_output_tokens=64, reasoning_effort="low"
)


def _completion(content: str | None, usage: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "id": "x",
        "object": "chat.completion",
        "created": 1,
        "model": "gemini-test-001",
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": content},
            }
        ],
        "usage": usage
        or {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
            "completion_tokens_details": {"reasoning_tokens": 2},
        },
    }


def _client(handler: Any) -> OpenAICompatibleClient:
    return OpenAICompatibleClient(
        base_url="https://llm.invalid/v1/",
        api_key="test-key",
        timeout_s=5,
        max_retries=0,
        http_client=httpx2.Client(transport=httpx2.MockTransport(handler)),
    )


def test_request_shape_and_usage_parsed(caplog: pytest.LogCaptureFixture) -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        seen["auth"] = request.headers.get("authorization")
        return httpx2.Response(200, json=_completion("Merhaba [K1]."))

    with caplog.at_level(logging.INFO, logger="app.services.llm"):
        response = _client(handler).complete(REQUEST)

    assert seen["url"] == "https://llm.invalid/v1/chat/completions"
    assert seen["auth"] == "Bearer test-key"
    body = seen["body"]
    assert body["model"] == "gemini-test"
    assert [m["role"] for m in body["messages"]] == ["system", "user"]
    assert body["messages"][0]["content"] == "sistem"
    assert body["max_completion_tokens"] == 64
    assert body["reasoning_effort"] == "low"
    assert body["temperature"] == 0.0

    assert response.text == "Merhaba [K1]."
    assert response.model == "gemini-test-001"
    assert (response.tokens_in, response.tokens_out, response.tokens_reasoning) == (10, 5, 2)
    assert response.finish_reason == "stop"

    record = next(r for r in caplog.records if r.getMessage() == "llm call")
    assert record.tokens_in == 10  # type: ignore[attr-defined]
    assert record.tokens_out == 5  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("status", "error"),
    [
        (401, LLMAuthError),
        (403, LLMAuthError),
        (429, LLMRateLimitError),
        (500, LLMUnavailableError),
    ],
)
def test_http_errors_map_to_llm_errors(status: int, error: type[Exception]) -> None:
    def handler(_: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(status, json={"error": {"message": "nope"}})

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
        return httpx2.Response(200, json=_completion(""))

    with pytest.raises(LLMResponseError):
        _client(handler).complete(REQUEST)


# The test container inherits the live `.env` (S1 set LLM_PROVIDER=anthropic): these two
# tests are about the openai_compatible branch of the factory, so pin the provider.
_OPENAI = {"llm_provider": "openai_compatible"}


def test_factory_without_key_is_not_configured(settings: Settings) -> None:
    with pytest.raises(LLMNotConfiguredError):
        build_llm_client(settings.model_copy(update={**_OPENAI, "llm_api_key": None}))
    with pytest.raises(LLMNotConfiguredError):
        build_llm_client(settings.model_copy(update={**_OPENAI, "llm_api_key": SecretStr("")}))


def test_factory_builds_openai_compatible_client(settings: Settings) -> None:
    client = build_llm_client(
        settings.model_copy(update={**_OPENAI, "llm_api_key": SecretStr("k")})
    )
    assert isinstance(client, OpenAICompatibleClient)


def test_rate_limit_logs_safe_error_body_without_key(caplog: pytest.LogCaptureFixture) -> None:
    """Adım 6 düzeltmesi (11.10.2026): 429'da hata gövdesi (RESOURCE_EXHAUSTED vb.) güvenli
    alanlarla loglanır; anahtar ("test-key") hiçbir kayıtta görünmez."""

    def handler(_: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            429,
            json={
                "error": {
                    "code": 429,
                    "message": "You exceeded your current quota.",
                    "status": "RESOURCE_EXHAUSTED",
                }
            },
        )

    with (
        caplog.at_level(logging.WARNING, logger="app.services.llm"),
        pytest.raises(LLMRateLimitError),
    ):
        _client(handler).complete(REQUEST)

    record = next(r for r in caplog.records if r.getMessage() == "llm rate limited (429)")
    assert "RESOURCE_EXHAUSTED" in record.error_body  # type: ignore[attr-defined]
    assert "429" in record.error_body  # type: ignore[attr-defined]
    for r in caplog.records:
        assert "test-key" not in r.getMessage()
        assert "test-key" not in str(getattr(r, "error_body", ""))


def test_503_logs_safe_error_body_without_key(caplog: pytest.LogCaptureFixture) -> None:
    def handler(_: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            503, json={"error": {"code": 503, "message": "overloaded", "status": "UNAVAILABLE"}}
        )

    with (
        caplog.at_level(logging.WARNING, logger="app.services.llm"),
        pytest.raises(LLMUnavailableError),
    ):
        _client(handler).complete(REQUEST)

    record = next(r for r in caplog.records if r.getMessage() == "llm unavailable (503)")
    assert "UNAVAILABLE" in record.error_body  # type: ignore[attr-defined]
    for r in caplog.records:
        assert "test-key" not in r.getMessage()
        assert "test-key" not in str(getattr(r, "error_body", ""))


def test_safe_error_summary_ignores_unknown_fields() -> None:
    """Whitelist dışı alanlar (örn. hayali bir 'request_headers' alanı) hiç okunmaz."""

    class _FakeExc:
        body = {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "request_headers": "SECRET"}}

    summary = _safe_error_summary(_FakeExc())  # type: ignore[arg-type]
    assert "SECRET" not in summary
    assert "RESOURCE_EXHAUSTED" in summary


def test_safe_error_summary_handles_missing_body() -> None:
    class _FakeExc:
        body = None

    assert _safe_error_summary(_FakeExc()) == "gövde yok/okunamadı"  # type: ignore[arg-type]
