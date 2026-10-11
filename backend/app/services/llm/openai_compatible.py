"""OpenAI-compatible chat client (openai SDK + `base_url`); default target is Gemini."""

from __future__ import annotations

import logging
import time

import httpx2
import openai
from openai.types.shared_params import ResponseFormatJSONObject

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


def _safe_error_summary(exc: openai.APIStatusError) -> str:
    """429/503 hata gövdesinden GÜVENLİ, bilinen alanları çıkarır (code/status/message/
    retryDelay) — API anahtarı, header veya istek içeriği ASLA okunmaz; ham gövde de
    basılmaz (bilinmeyen bir alanın yanlışlıkla hassas veri taşıma riskine karşı, yalnız
    whitelist'teki alan adları okunur). Adım 6 kota teşhisinde (11.10.2026) bu gövdenin
    hiçbir yerde loglanmadığı, bu yüzden hata türünün ("RESOURCE_EXHAUSTED" gibi) hiçbir
    yerde kayıtlı olmadığı görülmüştü — bu düzeltme o boşluğu kapatıyor. Retry/backoff
    mantığına dokunmuyor (SDK'nın kendi `max_retries`'ı), yalnız log ekliyor."""
    body = getattr(exc, "body", None)
    nested = body.get("error") if isinstance(body, dict) else None
    error = nested if isinstance(nested, dict) else body
    if not isinstance(error, dict):
        return "gövde yok/okunamadı"
    parts = []
    for key in ("code", "status", "message", "retryDelay", "retry_delay"):
        value = error.get(key)
        if value is None:
            continue
        text = str(value)
        if len(text) > 160:
            text = text[:160] + "…"
        parts.append(f"{key}={text}")
    return "; ".join(parts) if parts else "tanımlı alan yok"


class OpenAICompatibleClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout_s: float,
        max_retries: int = 1,
        http_client: httpx2.Client | None = None,
    ) -> None:
        # `max_retries` is the SDK's own backoff for 429/5xx (Gemini free-tier limits).
        self._client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_s,
            max_retries=max_retries,
            http_client=http_client,
        )

    def complete(self, request: LLMRequest) -> LLMResponse:
        started = time.perf_counter()
        # Omitted (not even `{"type": "text"}`) for the default case — keeps the exact
        # request payload `/api/ask` always sent, unchanged by this Phase 3.2 addition.
        response_format: ResponseFormatJSONObject | openai.Omit = (
            {"type": "json_object"} if request.response_format == "json_object" else openai.Omit()
        )
        try:
            completion = self._client.chat.completions.create(
                model=request.model,
                messages=[
                    {"role": "system", "content": request.system},
                    {"role": "user", "content": request.user},
                ],
                max_completion_tokens=request.max_output_tokens,
                temperature=request.temperature,
                reasoning_effort=request.reasoning_effort,
                response_format=response_format,
            )
        except (openai.AuthenticationError, openai.PermissionDeniedError) as exc:
            raise LLMAuthError(str(exc)) from exc
        except openai.RateLimitError as exc:
            log.warning("llm rate limited (429)", extra={"error_body": _safe_error_summary(exc)})
            raise LLMRateLimitError(str(exc)) from exc
        except openai.APITimeoutError as exc:
            raise LLMTimeoutError(str(exc)) from exc
        except openai.APIStatusError as exc:
            if exc.status_code == 503:
                log.warning("llm unavailable (503)", extra={"error_body": _safe_error_summary(exc)})
            raise LLMUnavailableError(str(exc)) from exc
        except openai.APIConnectionError as exc:
            raise LLMUnavailableError(str(exc)) from exc
        except openai.OpenAIError as exc:
            raise LLMError(str(exc)) from exc
        latency_ms = round((time.perf_counter() - started) * 1000)

        usage = completion.usage
        tokens_in = usage.prompt_tokens if usage else 0
        tokens_out = usage.completion_tokens if usage else 0
        tokens_reasoning = (
            usage.completion_tokens_details.reasoning_tokens
            if usage and usage.completion_tokens_details
            else None
        )
        choice = completion.choices[0] if completion.choices else None
        finish_reason = choice.finish_reason if choice else None
        text = (choice.message.content or "") if choice else ""

        log.info(
            "llm call",
            extra={
                "model": completion.model or request.model,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "tokens_reasoning": tokens_reasoning,
                "latency_ms": latency_ms,
                "finish_reason": finish_reason,
                "prompt_chars": len(request.system) + len(request.user),
            },
        )
        if not text.strip():
            raise LLMResponseError(f"empty completion (finish_reason={finish_reason!r})")
        return LLMResponse(
            text=text,
            model=completion.model or request.model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            tokens_reasoning=tokens_reasoning,
            finish_reason=finish_reason,
            latency_ms=latency_ms,
        )
