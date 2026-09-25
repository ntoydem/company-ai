from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.repositories.document_chunk_repo import RetrievedChunk
from app.schemas.retrieval import RetrievalFilters
from app.services import retrieval as retrieval_module
from app.services.embedding_client import EmbeddingError
from app.services.retrieval import _reciprocal_rank_fusion, retrieve
from tests.fakes import FakeEmbeddingClient


def _make_document(session: Session, *, title: str) -> Document:
    import uuid as _uuid

    document = Document(
        title=title,
        document_type="facility_agreement",
        counterparty="PQR Bank",
        document_date=date(2023, 6, 1),
        storage_path=f"{_uuid.uuid4()}/original.pdf",
    )
    session.add(document)
    session.flush()
    return document


def _add_chunk(session: Session, document: Document, *, page_number: int, text: str) -> None:
    session.add(
        DocumentChunk(document_id=document.id, chunk_index=0, page_number=page_number, text=text)
    )


def test_fts_finds_dscr_covenant_in_both_documents(db_session: Session, admin_user: User) -> None:
    """Kabul kriteri 4: FTS "DSCR covenant" -> chunks from both documents, page_number set."""
    executed = _make_document(db_session, title="Facility Agreement EXECUTED")
    amendment = _make_document(db_session, title="Amendment 01")
    _add_chunk(
        db_session,
        executed,
        page_number=3,
        text="Minimum DSCR covenant is 1.25x under this facility agreement.",
    )
    _add_chunk(
        db_session,
        amendment,
        page_number=2,
        text="The DSCR covenant is amended to a minimum of 1.20x.",
    )
    db_session.commit()

    results = retrieve(db_session, admin_user, "DSCR covenant", RetrievalFilters())

    document_ids = {chunk.document_id for chunk in results}
    assert executed.id in document_ids
    assert amendment.id in document_ids
    assert all(chunk.page_number is not None for chunk in results)


def test_empty_allowed_ids_yields_empty_retrieval(db_session: Session) -> None:
    """Kabul kriteri 5: allowed_document_ids() boş küme -> retrieve() boş liste.

    An inactive user is the real, already-tested path to an empty allowed set
    (app/services/authorization.py's Step-0 stub) — no fakes needed.
    """
    inactive_user = User(
        username="inactive-test-user",
        password_hash="x",
        display_name="Inactive",
        is_active=False,
    )
    assert retrieve(db_session, inactive_user, "DSCR covenant", RetrievalFilters()) == []


# --- Phase 3.4: hybrid retrieval (EMBEDDINGS_ENABLED=true) ---


def test_rrf_ranks_a_chunk_present_in_both_lists_above_either_alone() -> None:
    import uuid as _uuid

    shared = RetrievedChunk(
        id=_uuid.uuid4(), document_id=_uuid.uuid4(), chunk_index=0, page_number=1, text="", rank=0.9
    )
    fts_only = RetrievedChunk(
        id=_uuid.uuid4(), document_id=_uuid.uuid4(), chunk_index=0, page_number=1, text="", rank=0.5
    )
    vector_only = RetrievedChunk(
        id=_uuid.uuid4(), document_id=_uuid.uuid4(), chunk_index=0, page_number=1, text="", rank=0.5
    )
    # `shared` ranks 1st in FTS, 2nd in vector; the two singles each rank 1st in their
    # own list only — RRF must still put `shared` first (it scores from both lists).
    fused = _reciprocal_rank_fusion([[shared, fts_only], [vector_only, shared]])

    assert fused[0].id == shared.id
    assert {c.id for c in fused[1:]} == {fts_only.id, vector_only.id}


def test_rrf_keeps_a_chunk_present_in_only_one_list() -> None:
    import uuid as _uuid

    only = RetrievedChunk(
        id=_uuid.uuid4(), document_id=_uuid.uuid4(), chunk_index=0, page_number=1, text="", rank=0.1
    )
    fused = _reciprocal_rank_fusion([[only], []])
    assert [c.id for c in fused] == [only.id]


_QUERY_VECTOR = [1.0] + [0.0] * 1023


def test_embeddings_disabled_never_builds_embedding_client(
    db_session: Session, admin_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`EMBEDDINGS_ENABLED=false` (the test default) — the embedding client is never
    even constructed, let alone called (ADR-007: FTS-only must stay fully unaffected)."""

    def _must_not_be_built(_: object) -> None:
        raise AssertionError("build_embedding_client must not be called when disabled")

    monkeypatch.setattr(retrieval_module, "build_embedding_client", _must_not_be_built)
    document = _make_document(db_session, title="Facility Agreement")
    _add_chunk(db_session, document, page_number=1, text="DSCR covenant minimum 1.20x.")
    db_session.commit()

    results = retrieve(db_session, admin_user, "DSCR covenant", RetrievalFilters())

    assert document.id in {c.document_id for c in results}


def test_hybrid_retrieval_surfaces_a_vector_only_chunk(
    db_session: Session, admin_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A chunk with no FTS-matchable terms but a close embedding is still retrieved once
    hybrid search is active — the point of adding vector search at all."""
    document = _make_document(db_session, title="Vector-only document")
    _add_chunk(db_session, document, page_number=1, text="Tamamen alakasız bir cümle, terim yok.")
    db_session.commit()
    chunk_row = db_session.scalars(select(DocumentChunk)).one()
    chunk_row.embedding = _QUERY_VECTOR
    db_session.commit()

    fake = FakeEmbeddingClient()
    fake.default_vector = _QUERY_VECTOR
    monkeypatch.setattr(retrieval_module, "_embedding_client", lambda: fake)

    # A query with zero term overlap with the chunk's text — pure FTS would find nothing.
    results = retrieve(
        db_session,
        admin_user,
        "DSCR covenant",
        RetrievalFilters(),
        raw_question="Ankara RES DSCR covenant nedir?",
    )

    assert document.id in {c.document_id for c in results}
    assert fake.calls == [["Ankara RES DSCR covenant nedir?"]]


def test_hybrid_retrieval_falls_back_to_fts_when_embedding_call_fails(
    db_session: Session, admin_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SPEC_06 §8: a dead/slow embed service degrades to FTS-only, `retrieve()` never
    raises for this."""
    document = _make_document(db_session, title="Facility Agreement")
    _add_chunk(db_session, document, page_number=1, text="DSCR covenant minimum 1.20x.")
    db_session.commit()

    fake = FakeEmbeddingClient(error=EmbeddingError("embed service unreachable"))
    monkeypatch.setattr(retrieval_module, "_embedding_client", lambda: fake)

    results = retrieve(db_session, admin_user, "DSCR covenant", RetrievalFilters())

    assert document.id in {c.document_id for c in results}


def test_fts_tied_ranks_come_back_in_a_deterministic_order(
    db_session: Session, admin_user: User
) -> None:
    """Phase 3.2b: an OR query gives many chunks the exact same `ts_rank_cd`; without an
    explicit tie-break Postgres picked the `LIMIT` winners by heap order, so the same
    question could reach the LLM with a different page set on each call."""
    import uuid as _uuid

    from app.repositories.document_chunk_repo import search_fts

    document = _make_document(db_session, title="Tied")
    for page in range(1, 8):
        db_session.add(
            DocumentChunk(
                document_id=document.id,
                chunk_index=page,
                page_number=page,
                text=f"facility agreement page {page} covenant",
            )
        )
    db_session.commit()

    first = search_fts(db_session, allowed_ids=[document.id], query="facility OR covenant", top_k=3)
    second = search_fts(
        db_session, allowed_ids=[document.id], query="facility OR covenant", top_k=3
    )
    assert len({c.rank for c in first}) == 1  # genuinely tied
    assert [c.page_number for c in first] == [c.page_number for c in second] == [1, 2, 3]
    assert isinstance(document.id, _uuid.UUID)
