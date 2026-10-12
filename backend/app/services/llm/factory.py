"""Build the configured `LLMClient` from settings (`LLM_PROVIDER`)."""

from __future__ import annotations

from app.core.config import Settings
from app.services.llm.anthropic_client import AnthropicClient
from app.services.llm.base import LLMClient, LLMNotConfiguredError
from app.services.llm.openai_compatible import OpenAICompatibleClient


def build_llm_client(settings: Settings) -> LLMClient:
    if settings.llm_provider == "anthropic":
        # İş Emri 2026-10-11-C: Phase 0.3's "Deferred" artık dolduruldu. Anahtar her
        # zaman `PROSE_ANTHROPIC_API_KEY`'den gelir (ayar alanının kendi alias'ı
        # üzerinden) — `ANTHROPIC_API_KEY` adı burada hiç görünmez.
        api_key = (
            settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else ""
        )
        if not api_key:
            raise LLMNotConfiguredError("PROSE_ANTHROPIC_API_KEY is not set")
        return AnthropicClient(
            api_key=api_key,
            timeout_s=settings.llm_timeout_s,
            max_retries=settings.anthropic_max_retries,
            thinking=settings.anthropic_thinking,
        )
    api_key = settings.llm_api_key.get_secret_value() if settings.llm_api_key else ""
    if not api_key:
        raise LLMNotConfiguredError("LLM_API_KEY is not set")
    return OpenAICompatibleClient(
        base_url=settings.llm_base_url,
        api_key=api_key,
        timeout_s=settings.llm_timeout_s,
    )
