"""`document_chunks` search (FTS — ADR-007; vector — Phase 3.4) and the embedding
backfill queue."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import ColumnElement, Text, cast, func, literal, or_, select
from sqlalchemy.dialects.postgresql import REGCONFIG
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


@dataclass(frozen=True)
class DocumentHit:
    """One document's best-matching page for `GET /api/search` (B-14, Aşama D)."""

    document_id: uuid.UUID
    page_number: int
    snippet: str
    rank: float


# `ts_headline` options for search snippets: plain text, no markup — the chunk text is
# user-uploaded content, so the UI never has to render HTML from here (plan SORU 1).
_HEADLINE_OPTIONS = 'MaxWords=24, MinWords=10, StartSel="", StopSel=""'


def _fts_predicate(query: str) -> tuple[ColumnElement[float], ColumnElement[bool], object]:
    """The one FTS match definition shared by retrieval (`search_fts`) and search
    (`search_document_hits`): both tsvector configurations via `websearch_to_tsquery`,
    ranked by whichever matched best (`ts_rank_cd`). Returns (rank, where, turkish_query)."""
    turkish_query = func.websearch_to_tsquery("turkish", query)
    simple_query = func.websearch_to_tsquery("simple", query)
    rank = func.greatest(
        func.ts_rank_cd(DocumentChunk.tsv_turkish, turkish_query),
        func.ts_rank_cd(DocumentChunk.tsv_simple, simple_query),
    )
    where = or_(
        DocumentChunk.tsv_turkish.op("@@")(turkish_query),
        DocumentChunk.tsv_simple.op("@@")(simple_query),
    )
    return rank, where, turkish_query


def search_fts(
    session: Session, *, allowed_ids: Iterable[uuid.UUID], query: str, top_k: int
) -> list[RetrievedChunk]:
    """Search chunks belonging to `allowed_ids` only (ADR-004 gates before retrieval).

    Matches against both the `turkish` (stemmed) and `simple` (unstemmed) tsvector
    columns via `websearch_to_tsquery` — tolerant of stray punctuation, ANDs terms like a
    normal search box — and ranks by whichever config matched best. Cover-density ranking
    (`ts_rank_cd`) rewards chunks where several distinct query terms occur close together,
    which is what an OR query (ADR-020) needs: the clause stating the covenant outranks a
    cover page that merely lists the same words.
    """
    allowed = list(allowed_ids)
    if not allowed:
        return []

    rank_expr, where, _ = _fts_predicate(query)
    rank = rank_expr.label("rank")

    stmt = (
        select(DocumentChunk, rank)
        .where(DocumentChunk.document_id.in_(allowed))
        .where(where)
        # Deterministic tie-break: with OR queries many chunks share the exact same
        # `ts_rank_cd` (28 of 42 tied at 0.2 on a typical finance question, Phase 3.2b T1);
        # without it Postgres picks the LIMIT winners by heap order, so the same question
        # could reach the LLM with a different page set from one call to the next.
        .order_by(rank.desc(), DocumentChunk.document_id, DocumentChunk.chunk_index)
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


def search_document_hits(
    session: Session, *, allowed_ids: Iterable[uuid.UUID], query: str, limit: int
) -> list[DocumentHit]:
    """B-14: one hit per document — its best-ranked chunk — with a plain-text headline,
    best documents first. Same predicate as `search_fts`, so what Balbal would retrieve
    is what search finds; `retrieve()` itself is untouched. `ts_headline` runs only on
    the final ≤ `limit` rows."""
    allowed = list(allowed_ids)
    if not allowed or not query:
        return []
    rank_expr, where, turkish_query = _fts_predicate(query)
    best = (
        select(
            DocumentChunk.document_id.label("document_id"),
            DocumentChunk.page_number.label("page_number"),
            DocumentChunk.text.label("text"),
            rank_expr.label("rank"),
        )
        .where(DocumentChunk.document_id.in_(allowed))
        .where(where)
        .distinct(DocumentChunk.document_id)
        .order_by(DocumentChunk.document_id, rank_expr.desc(), DocumentChunk.chunk_index)
        .subquery("best")
    )
    # Postgres resolves ts_headline(regconfig, text, tsquery, text) only with exact types;
    # SQLAlchemy would otherwise bind the two literals as VARCHAR.
    headline = func.ts_headline(
        cast(literal("turkish"), REGCONFIG),
        best.c.text,
        turkish_query,
        cast(literal(_HEADLINE_OPTIONS), Text),
    )
    stmt = (
        select(best.c.document_id, best.c.page_number, headline, best.c.rank)
        .order_by(best.c.rank.desc(), best.c.document_id)
        .limit(limit)
    )
    return [
        DocumentHit(
            document_id=document_id, page_number=page_number, snippet=snippet, rank=float(rank)
        )
        for document_id, page_number, snippet, rank in session.execute(stmt).all()
    ]


def search_vector(
    session: Session, *, allowed_ids: Iterable[uuid.UUID], vector: list[float], top_k: int
) -> list[RetrievedChunk]:
    """Vector similarity search (Phase 3.4, `EMBEDDINGS_ENABLED=true` only) — same
    `allowed_ids` gate as `search_fts` (ADR-004). Chunks without an embedding yet (the
    backfill loop hasn't reached them) are excluded rather than surfaced with a
    meaningless distance. `rank` is cosine *similarity* (`1 - distance`, higher = better)
    so it sorts the same direction as `search_fts`'s `ts_rank_cd` — used only for
    single-list ordering; `retrieval.py`'s RRF fusion compares rank *position*, never
    these two scales directly against each other.
    """
    allowed = list(allowed_ids)
    if not allowed:
        return []

    distance = DocumentChunk.embedding.cosine_distance(vector)
    stmt = (
        select(DocumentChunk, distance.label("distance"))
        .where(DocumentChunk.document_id.in_(allowed))
        .where(DocumentChunk.embedding.is_not(None))
        .order_by(distance, DocumentChunk.document_id, DocumentChunk.chunk_index)
        .limit(top_k)
    )
    return [
        RetrievedChunk(
            id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
            text=chunk.text,
            rank=1.0 - float(distance_value),
        )
        for chunk, distance_value in session.execute(stmt).all()
    ]


def list_ids_pending_embedding(session: Session, *, limit: int) -> list[uuid.UUID]:
    """Chunks with no vector yet (Phase 3.4 embedding backfill queue), oldest first."""
    stmt = (
        select(DocumentChunk.id)
        .where(DocumentChunk.embedding.is_(None))
        .order_by(DocumentChunk.created_at)
        .limit(limit)
    )
    return list(session.scalars(stmt).all())


def get_many(session: Session, ids: Iterable[uuid.UUID]) -> list[DocumentChunk]:
    id_list = list(ids)
    if not id_list:
        return []
    return list(session.scalars(select(DocumentChunk).where(DocumentChunk.id.in_(id_list))).all())


def set_embedding(session: Session, chunk: DocumentChunk, vector: list[float]) -> None:
    chunk.embedding = vector
    session.commit()
