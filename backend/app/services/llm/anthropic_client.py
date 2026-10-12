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
3/3). So every call sends `thinking={"type": "disabled"}` unless `ANTHROPIC_THINKING=true`
(then `{"type": "adaptive"}`; see infra/.env.example). Measurement table in
docs/reports/IS_EMRI_2026-10-12K_B1F.md.
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
        # `thinking`: False (default) sends `{"type": "disabled"}` on every call — see the
        # module docstring; True opts into adaptive thinking (callers must then budget
        # `max_output_tokens` for it, the router's 300 is not enough).
        self._thinking: ThinkingConfigParam = (
            {"type": "adaptive"} if thinking else {"type": "disabled"}
        )
        # `max_retries`: the SDK's own backoff for 429/5xx (İş Emri 2026-10-11-C Adım 1 —
        # bu hesapta dakikada 1000 istek/2.400.000 token, agresif bir dış pacing'e gerek
        # yok; SDK'nın yerleşik üstel geri-çekilmesi yeterli).
        self._client = anthropic.Anthropic(
            api_key=api_key,
            timeout=timeout_s,
            max_retries=max_retries,
            http_client=http_client,
        )

    def complete(self, request: LLMRequest) -> LLMResponse:
        started = time.perf_counter()
        system = request.system
        if request.response_format == "json_object":
            system = system + _JSON_ONLY_SUFFIX
        try:
            # `messages.create()` has no `temperature` parameter in the installed SDK
            # (confirmed by introspection, 11.10.2026 — not in its `create()` signature at
            # all); `request.temperature` (Gemini-side determinism knob) has no Anthropic
            # equivalent here and is silently not forwarded.
            message = self._client.messages.create(
                model=request.model,
                max_tokens=request.max_output_tokens,
                system=system,
                messages=[{"role": "user", "content": request.user}],
                thinking=self._thinking,
            )
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as exc:
            raise LLMAuthError(str(exc)) from exc
        except anthropic.RateLimitError as exc:
            log.warning("llm rate limited (429)", extra={"error_body": _safe_error_summary(exc)})
            raise LLMRateLimitError(str(exc)) from exc
        except anthropic.APITimeoutError as exc:
            raise LLMTimeoutError(str(exc)) from exc
        except anthropic.APIStatusError as exc:
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
        latency_ms = round((time.perf_counter() - started) * 1000)

        # Only `text` blocks are the answer; `thinking` blocks (if the operator enabled
        # thinking, or a model ignores "disabled") are never surfaced.
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
                    f"written (thinking={self._thinking['type']})"
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
