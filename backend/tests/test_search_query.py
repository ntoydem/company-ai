"""`build_search_query` (ADR-020) — unit cases plus retrieval against the real T0 pages."""

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.document_chunk_repo import search_fts
from app.schemas.retrieval import RetrievalFilters
from app.services.retrieval import retrieve
from app.services.search_query import build_search_query
from tests.t0_fixtures import load_t0_documents

Q_CURRENT = "Ankara RES'in güncel minimum DSCR covenant'ı nedir?"
Q_INITIAL = "İlk DSCR covenant neydi?"
Q_IZMIR = "İzmir RES'in COD tarihi nedir?"


def test_apostrophe_suffixes_and_question_words_are_dropped() -> None:
    assert build_search_query(Q_CURRENT) == "Ankara OR RES OR güncel OR minimum OR DSCR OR covenant"
    assert build_search_query(Q_INITIAL) == "İlk OR DSCR OR covenant"
    assert build_search_query("Kredinin vadesi kaç yıl?") == "Kredinin OR vadesi OR yıl"


def test_duplicates_short_tokens_and_punctuation() -> None:
    assert build_search_query("DSCR, dscr; DSCR!! x 1,25x") == "DSCR OR 25x"


def test_only_stopwords_yields_empty_query() -> None:
    assert build_search_query("Bu ne? Hangisi mi?") == ""


def test_verbatim_question_finds_nothing_but_built_query_does(
    db_session: Session, admin_user: User
) -> None:
    """Documents the Phase 0.3 finding (plan §T1): AND semantics on a Turkish question
    match no English chunk; the OR query built here does."""
    facility, amendment = load_t0_documents(db_session)
    allowed = {facility.id, amendment.id}

    assert search_fts(db_session, allowed_ids=allowed, query=Q_CURRENT, top_k=20) == []
    hits = search_fts(
        db_session, allowed_ids=allowed, query=build_search_query(Q_CURRENT), top_k=20
    )
    assert hits, "OR query must match"
    assert hits[0].document_id == amendment.id and hits[0].page_number == 3
    assert {hit.document_id for hit in hits} == allowed


def test_initial_question_reaches_both_documents(db_session: Session, admin_user: User) -> None:
    facility, amendment = load_t0_documents(db_session)
    hits = retrieve(db_session, admin_user, build_search_query(Q_INITIAL), RetrievalFilters())
    assert {hit.document_id for hit in hits} == {facility.id, amendment.id}
    assert any(hit.document_id == facility.id and hit.page_number == 6 for hit in hits)


def test_izmir_question_returns_ankara_chunks_only(db_session: Session, admin_user: User) -> None:
    """OR semantics let "RES" match Ankara pages — so criterion 3 is decided by the LLM's
    rule-2/3 discipline (live test), not by empty retrieval."""
    load_t0_documents(db_session)
    hits = retrieve(db_session, admin_user, build_search_query(Q_IZMIR), RetrievalFilters())
    assert hits
    assert not any("İzmir" in hit.text or "Izmir" in hit.text for hit in hits)
