"""Full-text search over `document_chunks` (ADR-007)."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk


@dataclass(frozen=True)
class RetrievedChunk:
    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    page_number: int
    text: str
    rank: float


def search_fts(
    session: Session, *, allowed_ids: Iterable[uuid.UUID], query: str, top_k: int
) -> list[RetrievedChunk]:
    """Search chunks belonging to `allowed_ids` only (ADR-004 gates before retrieval).

    Matches against both the `turkish` (stemmed) and `simple` (unstemmed) tsvector
    columns via `websearch_to_tsquery` — tolerant of stray punctuation, ANDs terms like a
    normal search box — and ranks by whichever config matched best.
    """
    allowed = list(allowed_ids)
    if not allowed:
        return []

    turkish_query = func.websearch_to_tsquery("turkish", query)
    simple_query = func.websearch_to_tsquery("simple", query)
    rank = func.greatest(
        func.ts_rank(DocumentChunk.tsv_turkish, turkish_query),
        func.ts_rank(DocumentChunk.tsv_simple, simple_query),
    ).label("rank")

    stmt = (
        select(DocumentChunk, rank)
        .where(DocumentChunk.document_id.in_(allowed))
        .where(
            or_(
                DocumentChunk.tsv_turkish.op("@@")(turkish_query),
                DocumentChunk.tsv_simple.op("@@")(simple_query),
            )
        )
        .order_by(rank.desc())
        .limit(top_k)
    )
    return [
        RetrievedChunk(
            id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
            text=chunk.text,
            rank=float(rank_value),
        )
        for chunk, rank_value in session.execute(stmt).all()
    ]
