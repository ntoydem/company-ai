"""`LLMClient` protocol, request/response shapes and the error hierarchy (ADR-009).

Nothing outside `app/services/llm/` imports a vendor SDK; callers see only these types.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

ReasoningEffort = Literal["minimal", "low", "medium", "high"]
ResponseFormat = Literal["text", "json_object"]


@dataclass(frozen=True)
class LLMRequest:
    system: str
    user: str
    model: str
    max_output_tokens: int
    temperature: float = 0.0
    reasoning_effort: ReasoningEffort = "low"
    # "json_object" (Phase 3.2, metadata classification): the provider is asked to return
    # a single JSON object. "/api/ask" never sets this — plain text + [K#] labels stay
    # simpler to parse and don't need escaping for Turkish text (ADR-021).
    response_format: ResponseFormat = "text"


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str
    tokens_in: int
    tokens_out: int
    tokens_reasoning: int | None
    finish_reason: str | None
    latency_ms: int


class LLMClient(Protocol):
    def complete(self, request: LLMRequest) -> LLMResponse: ...


class LLMError(Exception):
    """Base class: the model could not produce a usable answer."""


class LLMNotConfiguredError(LLMError):
    """No API key / provider configured — the rest of the system keeps working."""


class LLMAuthError(LLMError):
    """The provider rejected the credentials (401/403)."""


class LLMRateLimitError(LLMError):
    """Provider quota or rate limit (429)."""


class LLMTimeoutError(LLMError):
    """No response within `LLM_TIMEOUT_S`."""


class LLMUnavailableError(LLMError):
    """Connection failure or provider-side error (5xx)."""


class LLMResponseError(LLMError):
    """The provider answered, but without usable text (empty choice, filtered, truncated)."""
