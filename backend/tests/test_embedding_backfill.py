"""`app/services/embedding_backfill.py` (Phase 3.4) — no real `embed` service, a fake
`EmbeddingClient` stands in (`tests/fakes.py`, same pattern as `FakeLLMClient`)."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services import embedding_backfill
from app.services.embedding_client import EmbeddingError
from tests.fakes import FakeEmbeddingClient


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
    session: Session, document: Document, *, index: int, text: str = "metin"
) -> DocumentChunk:
    chunk = DocumentChunk(document_id=document.id, chunk_index=index, page_number=1, text=text)
    session.add(chunk)
    session.flush()
    return chunk


def test_fetch_pending_chunks_only_returns_ones_without_a_vector(db_session: Session) -> None:
    document = _document(db_session)
    pending = _chunk(db_session, document, index=0)
    embedded = _chunk(db_session, document, index=1)
    embedded.embedding = [0.1] * 1024
    db_session.commit()

    chunks = embedding_backfill.fetch_pending_chunks(db_session, limit=10)

    assert [c.id for c in chunks] == [pending.id]


def test_run_pending_scan_embeds_every_chunk_in_the_batch(db_session: Session) -> None:
    document = _document(db_session)
    first = _chunk(db_session, document, index=0, text="birinci")
    second = _chunk(db_session, document, index=1, text="ikinci")
    db_session.commit()
    fake = FakeEmbeddingClient()

    processed = embedding_backfill.run_pending_scan(db_session, fake, limit=10)

    assert processed == 2
    assert fake.calls == [["birinci", "ikinci"]]
    db_session.expire_all()
    assert db_session.get(DocumentChunk, first.id).embedding is not None
    assert db_session.get(DocumentChunk, second.id).embedding is not None


def test_run_pending_scan_respects_the_limit(db_session: Session) -> None:
    document = _document(db_session)
    for i in range(5):
        _chunk(db_session, document, index=i)
    db_session.commit()
    fake = FakeEmbeddingClient()

    processed = embedding_backfill.run_pending_scan(db_session, fake, limit=2)

    assert processed == 2


def test_run_pending_scan_with_nothing_pending_does_not_call_the_client(
    db_session: Session,
) -> None:
    fake = FakeEmbeddingClient()
    assert embedding_backfill.run_pending_scan(db_session, fake, limit=10) == 0
    assert fake.calls == []


def test_run_pending_scan_failed_batch_is_logged_and_skipped_not_raised(
    db_session: Session,
) -> None:
    document = _document(db_session)
    _chunk(db_session, document, index=0)
    db_session.commit()
    fake = FakeEmbeddingClient(error=EmbeddingError("embed service unreachable"))

    processed = embedding_backfill.run_pending_scan(db_session, fake, limit=10)

    assert processed == 0
