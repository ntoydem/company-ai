"""`build_search_query` (ADR-020) — unit cases plus retrieval against real ledger pages
(Phase 3.1; previously the Adım 0 T0 pages)."""

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.document_chunk_repo import search_fts
from app.schemas.retrieval import RetrievalFilters
from app.services.retrieval import retrieve
from app.services.search_query import build_search_query
from tests.ledger_fixtures import load_ledger_documents

Q_CURRENT = "Ankara RES'in güncel minimum DSCR covenant'ı nedir?"
Q_INITIAL = "İlk DSCR covenant neydi?"
# Same question, but with a project anchor — the LLM-authored Financial Covenants
# section (Phase 3.1) doesn't happen to use the [[project_name]] placeholder, so a bare
# "İlk DSCR covenant neydi?" (no "Ankara"/"RES" token) has nothing to OR-match against
# on that specific page; every real golden question (questions.json) names the project.
Q_INITIAL_ANCHORED = "Ankara RES'in ilk DSCR covenant'ı neydi?"
Q_IZMIR = "İzmir RES'in COD tarihi nedir?"

_FACILITY_REF, _AMENDMENT_REF = "DOC-ANK-FIN-004", "DOC-ANK-FIN-005"


def test_apostrophe_suffixes_and_question_words_are_dropped() -> None:
    # Question terms first, glossary expansions (Phase 3.2b) after them.
    assert build_search_query(Q_CURRENT).startswith(
        "Ankara OR RES OR güncel OR minimum OR DSCR OR covenant OR "
    )
    assert build_search_query(Q_INITIAL).startswith("İlk OR DSCR OR covenant OR ")
    assert build_search_query("Kredinin vadesi kaç yıl?").startswith(
        "Kredinin OR vadesi OR yıl OR "
    )


def test_duplicates_short_tokens_and_punctuation() -> None:
    assert build_search_query("DSCR, dscr; DSCR!! x 1,25x").startswith("DSCR OR 25x")


def test_only_stopwords_yields_empty_query() -> None:
    assert build_search_query("Bu ne? Hangisi mi?") == ""


def test_verbatim_question_finds_nothing_but_built_query_does(
    db_session: Session, admin_user: User
) -> None:
    """Documents the Phase 0.3 finding (plan §T1): AND semantics on a Turkish question
    match no English chunk; the OR query built here does."""
    documents = load_ledger_documents(db_session, [_FACILITY_REF, _AMENDMENT_REF])
    allowed = {doc.id for doc in documents.values()}

    assert search_fts(db_session, allowed_ids=allowed, query=Q_CURRENT, top_k=20) == []
    hits = search_fts(
        db_session, allowed_ids=allowed, query=build_search_query(Q_CURRENT), top_k=20
    )
    assert hits, "OR query must match"
    assert {hit.document_id for hit in hits} == allowed


def test_initial_question_reaches_both_documents(db_session: Session, admin_user: User) -> None:
    """Doc-level reach only — unlike the T0 fixture, the LLM-authored "Financial
    Covenants" section doesn't happen to use the [[project_name]] placeholder, so that
    *specific page* isn't guaranteed to carry an "Ankara"/"RES" anchor token; which page
    within a matched document gets retrieved is a content-authoring nuance, not a
    contract of `retrieve()` (that's covered by `test_search_query.py`'s pure unit
    tests and `test_verbatim_question_finds_nothing_but_built_query_does` above)."""
    documents = load_ledger_documents(db_session, [_FACILITY_REF, _AMENDMENT_REF])

    hits = retrieve(
        db_session, admin_user, build_search_query(Q_INITIAL_ANCHORED), RetrievalFilters()
    )
    assert {hit.document_id for hit in hits} == set(doc.id for doc in documents.values())


def test_izmir_question_returns_ankara_chunks_only(db_session: Session, admin_user: User) -> None:
    """OR semantics let "RES" match Ankara pages — so criterion 3 is decided by the LLM's
    rule-2/3 discipline (live test), not by empty retrieval."""
    load_ledger_documents(db_session, [_FACILITY_REF, _AMENDMENT_REF])
    hits = retrieve(db_session, admin_user, build_search_query(Q_IZMIR), RetrievalFilters())
    assert hits
    assert not any("İzmir" in hit.text or "Izmir" in hit.text for hit in hits)
