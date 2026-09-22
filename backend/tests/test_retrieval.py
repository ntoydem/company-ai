from datetime import date

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.schemas.retrieval import RetrievalFilters
from app.services.retrieval import retrieve


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
