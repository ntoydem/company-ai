"""Anthropic Messages API client (ADR-009's second `LLM_PROVIDER` branch, İş Emri
2026-10-11-C). Mirrors `openai_compatible.py`'s shape/error-mapping exactly so callers
(`router.py`, `ask.py`, `excel_ask.py`, `metadata_suggestion.py`) never know which
provider answered them.

Anthropic has no `response_format=json_object` equivalent — when the caller asks for
JSON, the system prompt gets one extra sentence demanding it, and a markdown code fence
around the reply (Claude's own habit) is stripped before parsing. `reasoning_effort` is
not mapped to Claude's "extended thinking".

Thinking (İş Emri 2026-10-12K-B1F): on Haiku 5.5, omitting the `thinking` parameter runs
*adaptive* thinking by default, and the (hidden, empty-text) thinking block is billed as
output tokens — with the router's `max_tokens=300` it ate the whole budget 3/3 times and
the reply had no text block at all (`output_config={"effort": "low"}` did NOT help, also
3/3). So every call sends thinking *off* unless `ANTHROPIC_THINKING=true` (then
`{"type": "adaptive"}`; see infra/.env.example). Measurement table in
docs/reports/IS_EMRI_2026-10-12K_B1F.md.

"Off" is spelled per model (İş Emri 2026-10-13S0c, blocker fix): Haiku 5.5 takes only
`{"type": "disabled"}` (400 on `between_tools`), Sonnet 5.5 takes only
`{"type": "between_tools"}` (400 on `disabled`: "To turn thinking off on this model, send
between_tools"). Known models are mapped in `_THINKING_OFF_BY_MODEL`; an unknown model
first gets `disabled` and, if the API answers 400 asking for `between_tools`, is retried
once with it — logged (model + safe error summary, never the key) and remembered for the
rest of the process so the 400 is not repeated per call.

Per-call override (İş Emri 2026-10-13S0d): `LLMRequest.thinking` ("adaptive" | "off") beats
the client-wide setting for that one call; None keeps today's behaviour byte-identical. Only
`ask.py`'s document answer call sets it (ANSWER_THINKING=true), never the router or the
Excel plan call (K-B1 §4a budget risk).
"""

from __future__ import annotations

import logging
import time

import anthropic
import httpx2
from anthropic.types import ThinkingConfigParam

from app.services.llm.base import (
    LLMAuthError,
    LLMError,
    LLMRateLimitError,
    LLMRequest,
    LLMResponse,
    LLMResponseError,
    LLMTimeoutError,
    LLMUnavailableError,
)

log = logging.getLogger(__name__)

_JSON_ONLY_SUFFIX = (
    "\n\nReply with a single valid JSON object and nothing else — no markdown code "
    "fence, no commentary before or after it."
)

_THINKING_ADAPTIVE: ThinkingConfigParam = {"type": "adaptive"}
_THINKING_DISABLED: ThinkingConfigParam = {"type": "disabled"}
_THINKING_BETWEEN_TOOLS: ThinkingConfigParam = {"type": "between_tools"}
# How each known model spells "thinking off" (module docstring; verified 13.10.2026).
_THINKING_OFF_BY_MODEL: dict[str, ThinkingConfigParam] = {
    "claude-haiku-5-5": _THINKING_DISABLED,
    "claude-sonnet-5-5": _THINKING_BETWEEN_TOOLS,
}


class _ThinkingDisabledRejectedError(Exception):
    """400 whose message asks for `between_tools` instead of `disabled` (unknown model)."""


def _wants_between_tools(exc: anthropic.APIStatusError) -> bool:
    return exc.status_code == 400 and "between_tools" in _safe_error_summary(exc)


def _safe_error_summary(exc: anthropic.APIStatusError) -> str:
    """429/529/5xx hata gövdesinden GÜVENLİ, bilinen alanları çıkarır — anahtar, header
    veya istek içeriği ASLA okunmaz (openai_compatible.py::_safe_error_summary ile aynı
    whitelist deseni)."""
    body = getattr(exc, "body", None)
    nested = body.get("error") if isinstance(body, dict) else None
    error = nested if isinstance(nested, dict) else body
    if not isinstance(error, dict):
        return "gövde yok/okunamadı"
    parts = []
    for key in ("type", "message"):
        value = error.get(key)
        if value is None:
            continue
        text = str(value)
        if len(text) > 160:
            text = text[:160] + "…"
        parts.append(f"{key}={text}")
    return "; ".join(parts) if parts else "tanımlı alan yok"


def _strip_markdown_json_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        stripped = stripped.removesuffix("```").strip()
    return stripped


class AnthropicClient:
    def __init__(
        self,
        *,
        api_key: str,
        timeout_s: float,
        max_retries: int = 2,
        http_client: httpx2.Client | None = None,
        thinking: bool = False,
    ) -> None:
        # `thinking`: False (default) sends thinking *off* on every call, spelled per model
        # (`_thinking_for`, module docstring); True opts into adaptive thinking (callers
        # must then budget `max_output_tokens` for it, the router's 300 is not enough).
        self._thinking: ThinkingConfigParam | None = _THINKING_ADAPTIVE if thinking else None
        # Unknown models whose `disabled` was rejected once → `between_tools` from then on.
        self._thinking_off_learned: dict[str, ThinkingConfigParam] = {}
        # `max_retries`: the SDK's own backoff for 429/5xx (İş Emri 2026-10-11-C Adım 1 —
        # bu hesapta dakikada 1000 istek/2.400.000 token, agresif bir dış pacing'e gerek
        # yok; SDK'nın yerleşik üstel geri-çekilmesi yeterli).
        self._client = anthropic.Anthropic(
            api_key=api_key,
            timeout=timeout_s,
            max_retries=max_retries,
            http_client=http_client,
        )

    def _thinking_for(self, request: LLMRequest) -> ThinkingConfigParam:
        """Per-call `request.thinking` wins (S0-d: "adaptive" / "off"); otherwise the
        client-wide ANTHROPIC_THINKING setting. "Off" is always spelled per model."""
        if request.thinking == "adaptive":
            return _THINKING_ADAPTIVE
        if request.thinking is None and self._thinking is not None:
            return self._thinking
        learned = self._thinking_off_learned.get(request.model)
        if learned is not None:
            return learned
        return _THINKING_OFF_BY_MODEL.get(request.model, _THINKING_DISABLED)

    def _create(
        self, request: LLMRequest, system: str, thinking: ThinkingConfigParam
    ) -> anthropic.types.Message:
        """One `messages.create()` with the SDK errors mapped to the shared `LLMError`
        family. A 400 asking for `between_tools` (unknown model, `disabled` sent) is raised
        as `_ThinkingDisabledRejectedError` so `complete()` can retry once."""
        try:
            # `messages.create()` has no `temperature` parameter in the installed SDK
            # (confirmed by introspection, 11.10.2026 — not in its `create()` signature at
            # all); `request.temperature` (Gemini-side determinism knob) has no Anthropic
            # equivalent here and is silently not forwarded.
            return self._client.messages.create(
                model=request.model,
                max_tokens=request.max_output_tokens,
                system=system,
                messages=[{"role": "user", "content": request.user}],
                thinking=thinking,
            )
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as exc:
            raise LLMAuthError(str(exc)) from exc
        except anthropic.RateLimitError as exc:
            log.warning("llm rate limited (429)", extra={"error_body": _safe_error_summary(exc)})
            raise LLMRateLimitError(str(exc)) from exc
        except anthropic.APITimeoutError as exc:
            raise LLMTimeoutError(str(exc)) from exc
        except anthropic.APIStatusError as exc:
            if thinking["type"] == "disabled" and _wants_between_tools(exc):
                raise _ThinkingDisabledRejectedError() from exc
            if exc.status_code in (503, 529):
                log.warning(
                    f"llm unavailable ({exc.status_code})",
                    extra={"error_body": _safe_error_summary(exc)},
                )
            raise LLMUnavailableError(str(exc)) from exc
        except anthropic.APIConnectionError as exc:
            raise LLMUnavailableError(str(exc)) from exc
        except anthropic.AnthropicError as exc:
            raise LLMError(str(exc)) from exc

    def complete(self, request: LLMRequest) -> LLMResponse:
        started = time.perf_counter()
        system = request.system
        if request.response_format == "json_object":
            system = system + _JSON_ONLY_SUFFIX
        thinking = self._thinking_for(request)
        try:
            message = self._create(request, system, thinking)
        except _ThinkingDisabledRejectedError as rejected:
            cause = rejected.__cause__
            log.warning(
                "llm thinking=disabled rejected, retrying with between_tools",
                extra={
                    "model": request.model,
                    "error_body": _safe_error_summary(cause)
                    if isinstance(cause, anthropic.APIStatusError)
                    else "gövde yok/okunamadı",
                },
            )
            thinking = _THINKING_BETWEEN_TOOLS
            self._thinking_off_learned[request.model] = thinking
            message = self._create(request, system, thinking)
        latency_ms = round((time.perf_counter() - started) * 1000)

        # Only `text` blocks are the answer; `thinking` blocks (if the operator enabled
        # thinking, or a model ignores "off") are never surfaced.
        block_types = [block.type for block in message.content]
        text = "".join(block.text for block in message.content if block.type == "text")
        if request.response_format == "json_object":
            text = _strip_markdown_json_fence(text)
        tokens_in = message.usage.input_tokens if message.usage else 0
        tokens_out = message.usage.output_tokens if message.usage else 0
        finish_reason = message.stop_reason

        log.info(
            "llm call",
            extra={
                "model": message.model or request.model,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "tokens_reasoning": None,
                "latency_ms": latency_ms,
                "finish_reason": finish_reason,
                "prompt_chars": len(system) + len(request.user),
            },
        )
        if not text.strip():
            detail = f"empty completion (finish_reason={finish_reason!r}, blocks={block_types})"
            if finish_reason == "max_tokens" and "thinking" in block_types:
                # K-B1 §4a: the whole output budget went to a thinking block — raise
                # `max_output_tokens` or keep thinking disabled (ANTHROPIC_THINKING).
                detail += (
                    "; thinking block consumed the output budget before any text was "
                    f"written (thinking={thinking['type']})"
                )
            raise LLMResponseError(detail)
        return LLMResponse(
            text=text,
            model=message.model or request.model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            tokens_reasoning=None,
            finish_reason=finish_reason,
            latency_ms=latency_ms,
        )
