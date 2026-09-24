"""`TEIEmbeddingClient` against a mock HTTP transport — no network, no running `embed`
service (mirrors `tests/test_llm_client.py`'s pattern for `OpenAICompatibleClient`)."""

from __future__ import annotations

import json
from typing import Any

import httpx2
import pytest

from app.services.embedding_client import EmbeddingError, TEIEmbeddingClient


def _embeddings_response(vectors: list[list[float]]) -> dict[str, Any]:
    return {
        "object": "list",
        "model": "bge-m3",
        "data": [
            {"object": "embedding", "index": i, "embedding": v} for i, v in enumerate(vectors)
        ],
        "usage": {"prompt_tokens": 4, "total_tokens": 4},
    }


def _client(handler: Any) -> TEIEmbeddingClient:
    return TEIEmbeddingClient(
        base_url="http://embed.invalid",
        model="bge-m3",
        timeout_s=5,
        http_client=httpx2.Client(transport=httpx2.MockTransport(handler)),
    )


def test_embed_sends_texts_and_parses_vectors_in_order() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx2.Response(200, json=_embeddings_response([[0.1, 0.2], [0.3, 0.4]]))

    vectors = _client(handler).embed(["birinci metin", "ikinci metin"])

    assert seen["url"] == "http://embed.invalid/v1/embeddings"
    assert seen["body"]["model"] == "bge-m3"
    assert seen["body"]["input"] == ["birinci metin", "ikinci metin"]
    assert vectors == [[0.1, 0.2], [0.3, 0.4]]


def test_embed_reorders_by_index() -> None:
    """The provider may return items out of order; the client must not just zip them."""

    def handler(_: httpx2.Request) -> httpx2.Response:
        body = _embeddings_response([[9.0], [1.0]])
        body["data"] = list(reversed(body["data"]))  # index 1 arrives first
        return httpx2.Response(200, json=body)

    vectors = _client(handler).embed(["a", "b"])

    assert vectors == [[9.0], [1.0]]


def test_embed_empty_input_returns_empty_without_a_call() -> None:
    def handler(_: httpx2.Request) -> httpx2.Response:
        raise AssertionError("should not be called")

    assert _client(handler).embed([]) == []


def test_connection_error_raises_embedding_error() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("connection refused", request=request)

    with pytest.raises(EmbeddingError):
        _client(handler).embed(["x"])


def test_mismatched_vector_count_raises_embedding_error() -> None:
    def handler(_: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json=_embeddings_response([[1.0]]))  # only 1, asked for 2

    with pytest.raises(EmbeddingError):
        _client(handler).embed(["a", "b"])
