"""`document_chunks` repo: vector search and the embedding backfill queue (Phase 3.4).
FTS (`search_fts`) is covered by `tests/test_retrieval.py`."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import EMBEDDING_DIM, DocumentChunk
from app.repositories import document_chunk_repo

_NEAR = [1.0] + [0.0] * (EMBEDDING_DIM - 1)
_FAR = [0.0, 1.0] + [0.0] * (EMBEDDING_DIM - 2)


def _document(session: Session) -> Document:
    document = Document(
        title="t",
        document_type="dt",
        counterparty="c",
        document_date=date(2023, 1, 1),
        storage_path=f"{uuid.uuid4()}/original.pdf",
    )
    session.add(document)
    session.flush()
    return document


def _chunk(
    session: Session, document: Document, *, index: int, embedding: list[float] | None
) -> DocumentChunk:
    chunk = DocumentChunk(
        document_id=document.id, chunk_index=index, page_number=1, text=f"chunk {index}"
    )
    chunk.embedding = embedding
    session.add(chunk)
    session.flush()
    return chunk


def test_search_vector_orders_by_cosine_distance_and_skips_null_embeddings(
    db_session: Session,
) -> None:
    document = _document(db_session)
    near = _chunk(db_session, document, index=0, embedding=_NEAR)
    far = _chunk(db_session, document, index=1, embedding=_FAR)
    _chunk(db_session, document, index=2, embedding=None)  # not yet backfilled
    db_session.commit()

    results = document_chunk_repo.search_vector(
        db_session, allowed_ids=[document.id], vector=_NEAR, top_k=10
    )

    assert [r.id for r in results] == [near.id, far.id]
    assert results[0].rank > results[1].rank  # higher = more similar


def test_search_vector_respects_allowed_ids(db_session: Session) -> None:
    allowed = _document(db_session)
    other = _document(db_session)
    _chunk(db_session, allowed, index=0, embedding=_NEAR)
    hidden = _chunk(db_session, other, index=0, embedding=_NEAR)
    db_session.commit()

    results = document_chunk_repo.search_vector(
        db_session, allowed_ids=[allowed.id], vector=_NEAR, top_k=10
    )

    assert hidden.id not in {r.id for r in results}


def test_search_vector_empty_allowed_ids_returns_empty(db_session: Session) -> None:
    assert (
        document_chunk_repo.search_vector(db_session, allowed_ids=[], vector=_NEAR, top_k=10) == []
    )


def test_list_ids_pending_embedding_only_returns_null_embeddings(db_session: Session) -> None:
    document = _document(db_session)
    pending = _chunk(db_session, document, index=0, embedding=None)
    _chunk(db_session, document, index=1, embedding=_NEAR)
    db_session.commit()

    ids = document_chunk_repo.list_ids_pending_embedding(db_session, limit=10)

    assert ids == [pending.id]


def test_set_embedding_persists_vector(db_session: Session) -> None:
    document = _document(db_session)
    chunk = _chunk(db_session, document, index=0, embedding=None)
    db_session.commit()

    document_chunk_repo.set_embedding(db_session, chunk, _NEAR)
    db_session.expire_all()

    refreshed = db_session.get(DocumentChunk, chunk.id)
    assert refreshed is not None
    assert refreshed.embedding is not None
    assert list(refreshed.embedding) == _NEAR
