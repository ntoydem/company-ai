"""Document persistence: creation, listing, and the ADR-004 `DocumentIdsProvider`."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Confidentiality, Document, DocumentSource, IngestionStatus
from app.models.document import DocumentStatus as DocStatus
from app.models.document_page import DocumentPage
from app.models.ingestion_job import IngestionJob, IngestionJobStatus
from app.schemas.authorization import AuthorizationScope


class SqlDocumentIdsProvider:
    """`DocumentIdsProvider` (ADR-004) backed by `documents`, filtered at the SQL level
    (ADR-007) — scope only narrows, matching fields are ANDed, absent ones are ignored."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_document_ids(self, scope: AuthorizationScope) -> Iterable[uuid.UUID]:
        stmt = select(Document.id)
        if scope.department is not None:
            stmt = stmt.where(Document.department == scope.department)
        if scope.project_id is not None:
            stmt = stmt.where(Document.project_id == scope.project_id)
        return self._session.scalars(stmt).all()

    def list_document_ids_for_departments(
        self,
        *,
        department_slugs: Iterable[str] | None,
        confidentiality_levels: Iterable[Confidentiality],
    ) -> Iterable[uuid.UUID]:
        """Role-based candidate set (Phase 1.2): `department_slugs=None` means every
        department (`management`); otherwise only those departments' documents."""
        stmt = select(Document.id).where(Document.confidentiality.in_(list(confidentiality_levels)))
        if department_slugs is not None:
            stmt = stmt.where(Document.department.in_(list(department_slugs)))
        return self._session.scalars(stmt).all()


def create_with_job(
    session: Session,
    *,
    document_id: uuid.UUID,
    title: str,
    document_type: str,
    document_date: date,
    counterparty: str,
    status: DocStatus,
    tags: list[str],
    storage_path: str,
    uploaded_by_id: uuid.UUID | None,
    effective_date: date | None = None,
    version: int = 1,
    supersedes_document_id: uuid.UUID | None = None,
    department: str | None = None,
    subdepartment: str | None = None,
    project_id: uuid.UUID | None = None,
    confidentiality: Confidentiality = Confidentiality.normal,
    source: DocumentSource = DocumentSource.web,
    related_document_ids: list[uuid.UUID] | None = None,
    external_ref: str | None = None,
) -> Document:
    """Create `documents` + the initial `ingestion_jobs` row together — one is never
    committed without the other (ADR-006). The upload endpoint (Phase 0.2) only ever
    passes the first block of keyword arguments; `department`/`project_id`/
    `confidentiality`/`source`/`related_document_ids`/`external_ref` exist for the
    Phase 3.1 demo seed (and, later, Phase 3.2's metadata-suggestion acceptance flow) —
    the upload form still does not accept them."""
    document = Document(
        id=document_id,
        title=title,
        document_type=document_type,
        document_date=document_date,
        counterparty=counterparty,
        status=status,
        tags=tags,
        effective_date=effective_date,
        version=version,
        supersedes_document_id=supersedes_document_id,
        department=department,
        subdepartment=subdepartment,
        project_id=project_id,
        source=source,
        confidentiality=confidentiality,
        related_document_ids=related_document_ids or [],
        external_ref=external_ref,
        storage_path=storage_path,
        ingestion_status=IngestionStatus.uploaded,
        uploaded_by_id=uploaded_by_id,
    )
    session.add(document)
    session.flush()
    session.add(IngestionJob(document_id=document.id, status=IngestionJobStatus.queued))
    session.flush()
    return document


def create_ready(
    session: Session,
    *,
    document_id: uuid.UUID,
    title: str,
    document_type: str,
    document_date: date,
    counterparty: str,
    status: DocStatus,
    tags: list[str],
    storage_path: str,
    uploaded_by_id: uuid.UUID | None,
    page_count: int | None,
    has_macros: bool = False,
    file_name: str | None = None,
    effective_date: date | None = None,
    version: int = 1,
    department: str | None = None,
    subdepartment: str | None = None,
    project_id: uuid.UUID | None = None,
    confidentiality: Confidentiality = Confidentiality.normal,
    source: DocumentSource = DocumentSource.web,
    related_document_ids: list[uuid.UUID] | None = None,
    external_ref: str | None = None,
) -> Document:
    """Excel family (Phase 4.2, SPEC_04 §1): no OCR job, no pages/chunks — the file is
    `ready` at once; sheets are read at query time by `app/excel/`. `page_count` = sheet
    count, informational only."""
    document = Document(
        id=document_id,
        title=title,
        document_type=document_type,
        document_date=document_date,
        counterparty=counterparty,
        status=status,
        tags=tags,
        effective_date=effective_date,
        version=version,
        department=department,
        subdepartment=subdepartment,
        project_id=project_id,
        source=source,
        confidentiality=confidentiality,
        related_document_ids=related_document_ids or [],
        external_ref=external_ref,
        storage_path=storage_path,
        ingestion_status=IngestionStatus.ready,
        uploaded_by_id=uploaded_by_id,
        page_count=page_count,
        has_macros=has_macros,
        file_name=file_name,
    )
    session.add(document)
    session.flush()
    return document


EXCEL_SUFFIXES = (".xlsx", ".xlsm", ".csv")


def list_excel_by_ids(session: Session, ids: Iterable[uuid.UUID]) -> list[Document]:
    """Ready Excel-family documents among `ids` (Phase 4.2 catalogue), title order."""
    id_list = list(ids)
    if not id_list:
        return []
    stmt = (
        select(Document)
        .where(Document.id.in_(id_list), Document.ingestion_status == IngestionStatus.ready)
        .order_by(Document.title)
    )
    return [
        d for d in session.scalars(stmt).all() if d.storage_path.lower().endswith(EXCEL_SUFFIXES)
    ]


def get_by_external_ref(session: Session, external_ref: str) -> Document | None:
    return session.scalar(select(Document).where(Document.external_ref == external_ref))


def list_ids_pending_suggestion(session: Session, *, limit: int) -> list[uuid.UUID]:
    """`ready` documents with no suggestion attempt yet (`ai_suggestion_id IS NULL`),
    oldest first (Phase 3.2 metadata-suggestion queue)."""
    stmt = (
        select(Document.id)
        .where(Document.ingestion_status == IngestionStatus.ready)
        .where(Document.ai_suggestion_id.is_(None))
        .order_by(Document.created_at)
        .limit(limit)
    )
    return list(session.scalars(stmt).all())


def apply_partial_update(session: Session, document: Document, updates: dict[str, object]) -> None:
    """Writes exactly the given attribute/value pairs to `document` (Phase 3.2 metadata
    suggestion apply). Validation of each value (department slug, project existence, …)
    is the caller's job — this function trusts what it is given."""
    for attribute, value in updates.items():
        setattr(document, attribute, value)
    session.flush()


def get_leading_page_text(session: Session, document_id: uuid.UUID, *, max_pages: int) -> str:
    """The first `max_pages` pages' text, joined — enough for cover/summary content
    without sending an entire document to the classifier (Phase 3.2)."""
    stmt = (
        select(DocumentPage.text)
        .where(DocumentPage.document_id == document_id)
        .order_by(DocumentPage.page_number)
        .limit(max_pages)
    )
    return "\n\n".join(session.scalars(stmt).all())


def get(session: Session, document_id: uuid.UUID) -> Document | None:
    return session.get(Document, document_id)


def list_by_ids(session: Session, ids: Iterable[uuid.UUID]) -> list[Document]:
    id_list = list(ids)
    if not id_list:
        return []
    stmt = select(Document).where(Document.id.in_(id_list)).order_by(Document.created_at.desc())
    return list(session.scalars(stmt).all())


def get_many(session: Session, ids: Iterable[uuid.UUID]) -> list[Document]:
    id_list = list(ids)
    if not id_list:
        return []
    return list(session.scalars(select(Document).where(Document.id.in_(id_list))).all())


def load_with_chains(
    session: Session, ids: Iterable[uuid.UUID], *, allowed_ids: set[uuid.UUID]
) -> list[Document]:
    """`ids` plus every `supersedes` / `superseded_by` chain member reachable from them,
    restricted to `allowed_ids` at every hop (ADR-004: a link to a document the user may
    not see is followed by id only, never loaded)."""
    loaded: dict[uuid.UUID, Document] = {}
    frontier = {document_id for document_id in ids if document_id in allowed_ids}
    while frontier:
        batch = get_many(session, frontier)
        frontier = set()
        for document in batch:
            loaded[document.id] = document
            for neighbour in (document.supersedes_document_id, document.superseded_by_document_id):
                if neighbour is not None and neighbour in allowed_ids and neighbour not in loaded:
                    frontier.add(neighbour)
    return list(loaded.values())


_SUPERSEDABLE_STATUSES = frozenset({DocStatus.draft, DocStatus.executed, DocStatus.amended})


def mark_superseded(session: Session, *, older: Document, newer: Document) -> None:
    """Close the chain link: `older` is now superseded by `newer` (Phase 3.2). `older.status`
    moves to `superseded` unless it is already `superseded` or `active` — `active` is an
    operational (not lifecycle) state and is left to whatever process manages it."""
    older.superseded_by_document_id = newer.id
    if older.status in _SUPERSEDABLE_STATUSES:
        older.status = DocStatus.superseded
    session.flush()
