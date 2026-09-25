"""`retrieve()`: authorize first (ADR-004), then full-text search (ADR-007), optionally
fused with a vector search when `EMBEDDINGS_ENABLED=true` (Phase 3.4)."""

from __future__ import annotations

import logging
import time
from dataclasses import replace
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User
from app.repositories.document_chunk_repo import RetrievedChunk, search_fts, search_vector
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.authorization import AuthorizationScope
from app.schemas.retrieval import RetrievalFilters
from app.services.authorization import allowed_document_ids
from app.services.embedding_client import EmbeddingClient, EmbeddingError, build_embedding_client

log = logging.getLogger(__name__)

# Standard IR default (Cormack et al.) — no score calibration needed, only rank order.
_RRF_K = 60


def _embedding_client() -> EmbeddingClient | None:
    """Built fresh per call, not cached: request volume is LAN/demo-scale (ADR-001), and
    a plain module function keeps this trivially overridable in tests
    (`monkeypatch.setattr(retrieval_module, "_embedding_client", ...)`, the same pattern
    already used for `allowed_document_ids` in `tests/test_ask.py`). Returns `None`
    (not an error) when the flag is off — hybrid search is an enhancement, not a
    requirement (ADR-007: FTS-only is the reference configuration)."""
    settings = get_settings()
    if not settings.embeddings_enabled:
        return None
    return build_embedding_client(settings)


def _reciprocal_rank_fusion(result_lists: list[list[RetrievedChunk]]) -> list[RetrievedChunk]:
    """Combines ranked lists by position only (`1/(k+rank)`), never by raw score — a
    `ts_rank_cd` value and a cosine similarity live on incomparable scales, so summing
    them directly would be unsound. A chunk present in only one list still scores from
    that list's term alone."""
    scores: dict[UUID, float] = {}
    by_id: dict[UUID, RetrievedChunk] = {}
    for chunks in result_lists:
        for position, chunk in enumerate(chunks, start=1):
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (_RRF_K + position)
            by_id.setdefault(chunk.id, chunk)
    ordered = sorted(scores, key=lambda chunk_id: scores[chunk_id], reverse=True)
    return [replace(by_id[chunk_id], rank=scores[chunk_id]) for chunk_id in ordered]


def retrieve(
    session: Session,
    user: User,
    question: str,
    filters: RetrievalFilters,
    *,
    raw_question: str | None = None,
) -> list[RetrievedChunk]:
    """`question` is the pre-built FTS query (`build_search_query()`'s OR-joined terms,
    ADR-020); `raw_question` is the natural-language question, used only for the
    embedding lookup (semantic similarity needs the real sentence, not stripped
    keywords) — defaults to `question` when the caller has nothing better (e.g. tests
    that pass a hand-picked FTS string directly)."""
    scope = AuthorizationScope(department=filters.department, project_id=filters.project_id)
    provider = SqlDocumentIdsProvider(session)
    allowed = allowed_document_ids(user, scope, provider)
    if not allowed:
        return []

    top_k = get_settings().retrieval_top_k
    client = _embedding_client()
    # Hybrid: fetch each leg deeper than the final cut. With both legs capped at top_k,
    # RRF (k=60) can never let a chunk found by one leg only past a chunk both legs found
    # — 1/61 < 2/(60+top_k) for any top_k < 62 — so a page only the vector leg finds was
    # dropped at the cut (Phase 3.2b §4 diagnosis). Depth 2×top_k keeps the cut honest.
    leg_k = top_k if client is None else 2 * top_k
    started = time.perf_counter()
    fts_chunks = search_fts(session, allowed_ids=allowed, query=question, top_k=leg_k)
    fts_ms = round((time.perf_counter() - started) * 1000)

    if client is None:
        _explain(fts_ms=fts_ms, fts=fts_chunks)
        return fts_chunks

    started = time.perf_counter()
    try:
        vectors = client.embed([raw_question or question])
    except EmbeddingError as exc:
        # SPEC_06 §8: a dead/slow embed service degrades this feature, not the whole
        # answer — fall back to FTS-only rather than failing `/api/ask`.
        log.warning("embedding lookup failed, falling back to FTS-only", extra={"error": str(exc)})
        _explain(fts_ms=fts_ms, fts=fts_chunks, fallback=True)
        return fts_chunks[:top_k]
    embed_ms = round((time.perf_counter() - started) * 1000)

    started = time.perf_counter()
    vector_chunks = search_vector(session, allowed_ids=allowed, vector=vectors[0], top_k=leg_k)
    vector_ms = round((time.perf_counter() - started) * 1000)
    if not vector_chunks:
        _explain(fts_ms=fts_ms, fts=fts_chunks, embed_ms=embed_ms, vector_ms=vector_ms)
        return fts_chunks[:top_k]
    fused = _reciprocal_rank_fusion([fts_chunks, vector_chunks])[:top_k]
    _explain(
        fts_ms=fts_ms,
        fts=fts_chunks,
        embed_ms=embed_ms,
        vector_ms=vector_ms,
        vector=vector_chunks,
        fused=fused,
    )
    return fused


def _pages(chunks: list[RetrievedChunk]) -> list[str]:
    return [f"{c.document_id}:{c.page_number}" for c in chunks]


def _explain(
    *,
    fts_ms: int,
    fts: list[RetrievedChunk],
    embed_ms: int | None = None,
    vector_ms: int | None = None,
    vector: list[RetrievedChunk] | None = None,
    fused: list[RetrievedChunk] | None = None,
    fallback: bool = False,
) -> None:
    """One structured line per retrieval — per-leg timings and page lists (Phase 3.2b
    §4 diagnosis: "did the vector leg find the page, and did fusion drop it?")."""
    log.info(
        "retrieval explain",
        extra={
            "fts_ms": fts_ms,
            "embed_ms": embed_ms,
            "vector_ms": vector_ms,
            "fallback": fallback,
            "fts_top": _pages(fts),
            "vector_top": _pages(vector) if vector is not None else None,
            "fused_top": _pages(fused) if fused is not None else None,
        },
    )
