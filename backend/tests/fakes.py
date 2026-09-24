"""Test doubles shared across test modules."""

from __future__ import annotations

from collections.abc import Callable

from app.models.document_chunk import EMBEDDING_DIM
from app.services.embedding_client import EmbeddingError
from app.services.llm import LLMError, LLMRequest, LLMResponse


class FakeLLMClient:
    """Records every request; replies from a queue, or from `reply_fn(request)` when set
    (default: a one-citation answer)."""

    def __init__(self, replies: list[str] | None = None, error: LLMError | None = None) -> None:
        self.requests: list[LLMRequest] = []
        self.replies = list(replies or [])
        self.reply_fn: Callable[[LLMRequest], str] | None = None
        self.error = error

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        if self.reply_fn is not None:
            text = self.reply_fn(request)
        else:
            text = self.replies.pop(0) if self.replies else "Cevap [K1]."
        return LLMResponse(
            text=text,
            model="fake-model",
            tokens_in=123,
            tokens_out=45,
            tokens_reasoning=None,
            finish_reason="stop",
            latency_ms=1,
        )

    def prompt_text(self, index: int = 0) -> str:
        request = self.requests[index]
        return request.system + "\n" + request.user


class FakeEmbeddingClient:
    """Records every call; returns a deterministic vector per text (or raises `error`)."""

    def __init__(self, *, error: EmbeddingError | None = None) -> None:
        self.calls: list[list[str]] = []
        self.error = error
        self.vector_by_text: dict[str, list[float]] = {}
        # Real dimension (bge-m3 via TEI) — a real `document_chunks.embedding` write
        # rejects anything else.
        self.default_vector: list[float] = [1.0] + [0.0] * (EMBEDDING_DIM - 1)

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        if self.error is not None:
            raise self.error
        return [self.vector_by_text.get(text, self.default_vector) for text in texts]
