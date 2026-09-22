"""Build the configured `LLMClient` from settings (`LLM_PROVIDER`)."""

from __future__ import annotations

from app.core.config import Settings
from app.services.llm.base import LLMClient, LLMNotConfiguredError
from app.services.llm.openai_compatible import OpenAICompatibleClient


def build_llm_client(settings: Settings) -> LLMClient:
    if settings.llm_provider == "anthropic":
        # Deferred (Phase 0.3 decision): revisit at the Phase 4.3 model decision point.
        raise LLMNotConfiguredError("LLM_PROVIDER=anthropic is not available in V0 yet")
    api_key = settings.llm_api_key.get_secret_value() if settings.llm_api_key else ""
    if not api_key:
        raise LLMNotConfiguredError("LLM_API_KEY is not set")
    return OpenAICompatibleClient(
        base_url=settings.llm_base_url,
        api_key=api_key,
        timeout_s=settings.llm_timeout_s,
    )
