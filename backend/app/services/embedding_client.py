"""Embedding client for the optional `embed` service (bge-m3 via TEI, Phase 3.4).

A single small module rather than a multi-provider package like `app/services/llm/` —
there is exactly one provider (Hugging Face Text Embeddings Inference serving bge-m3);
a provider-swap abstraction would be premature (docs/plans/PHASE_3_4_PLAN.md §4).
Never imported/constructed unless `EMBEDDINGS_ENABLED=true` (ADR-007): no connection is
attempted at import time, so `make test`'s default (`false`) never touches this module's
network code.
"""

from __future__ import annotations

import logging
from typing import Protocol

import httpx2
import openai

from app.core.config import Settings

log = logging.getLogger(__name__)


class EmbeddingError(Exception):
    """The embed service could not be reached, timed out, or returned unusable data."""


class EmbeddingClient(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class TEIEmbeddingClient:
    """Hugging Face Text Embeddings Inference's OpenAI-compatible `/v1/embeddings`
    endpoint (https://huggingface.co/docs/text-embeddings-inference/en/quick_tour) —
    same `openai` SDK + `base_url` pattern as `app/services/llm/openai_compatible.py`
    (ADR-009), pointed at the compose-internal `embed` service instead of Gemini.
    """

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_s: float,
        http_client: httpx2.Client | None = None,
    ) -> None:
        # TEI does not check the API key (self-hosted, no auth by default); the openai
        # SDK still requires a non-empty string to construct the client. `http_client`
        # lets tests swap in an `httpx2.MockTransport` (no network), same as
        # `app/services/llm/openai_compatible.py::OpenAICompatibleClient`.
        self._client = openai.OpenAI(
            api_key="not-required",
            base_url=f"{base_url}/v1",
            timeout=timeout_s,
            max_retries=1,
            http_client=http_client,
        )
        self._model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = self._client.embeddings.create(model=self._model, input=texts)
        except openai.OpenAIError as exc:
            raise EmbeddingError(str(exc)) from exc
        by_index = {item.index: item.embedding for item in response.data}
        if len(by_index) != len(texts):
            raise EmbeddingError(f"expected {len(texts)} vectors, got {len(by_index)}")
        return [list(by_index[i]) for i in range(len(texts))]


def build_embedding_client(settings: Settings) -> EmbeddingClient:
    return TEIEmbeddingClient(
        base_url=settings.embed_base_url,
        model=settings.embed_model_id,
        timeout_s=settings.embed_timeout_s,
    )
