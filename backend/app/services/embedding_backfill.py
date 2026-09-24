"""Embedding backfill (Phase 3.4, `EMBEDDINGS_ENABLED=true` only).

Populates `document_chunks.embedding` for chunks that have none yet, in small batches,
via the background loop in `app/main.py`. Deliberately decoupled from ingestion —
`ocr-worker` stays unaware of the `embed` service (docs/plans/PHASE_3_4_PLAN.md T4);
a document is searchable via FTS as soon as it is `ready`, and gains vector search a
little later once this loop reaches its chunks.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.repositories import document_chunk_repo
from app.services.embedding_client import EmbeddingClient, EmbeddingError

log = logging.getLogger(__name__)


def fetch_pending_chunks(session: Session, *, limit: int) -> list[DocumentChunk]:
    ids = document_chunk_repo.list_ids_pending_embedding(session, limit=limit)
    return document_chunk_repo.get_many(session, ids)


def run_pending_scan(session: Session, client: EmbeddingClient, *, limit: int) -> int:
    """One batch: embeds up to `limit` chunks with no vector yet. Returns how many were
    embedded. A failed `embed()` call for the whole batch is logged and skipped this
    tick (retried next tick) — never raises (ADR-006 pattern: a backfill failure never
    breaks anything else, embeddings are an enhancement, not a requirement)."""
    chunks = fetch_pending_chunks(session, limit=limit)
    if not chunks:
        return 0
    try:
        vectors = client.embed([chunk.text for chunk in chunks])
    except EmbeddingError as exc:
        log.warning(
            "embedding backfill batch failed", extra={"error": str(exc), "count": len(chunks)}
        )
        return 0
    for chunk, vector in zip(chunks, vectors, strict=True):
        document_chunk_repo.set_embedding(session, chunk, vector)
    return len(chunks)
