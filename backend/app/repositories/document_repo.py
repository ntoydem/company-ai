"""Document persistence: creation, listing, and the ADR-004 `DocumentIdsProvider`."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Confidentiality, Document, DocumentSource, IngestionStatus
from app.models.document import DocumentStatus as DocStatus
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
) -> Document:
    """Create `documents` + the initial `ingestion_jobs` row together — one is never
    committed without the other (ADR-006)."""
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
        source=DocumentSource.web,
        confidentiality=Confidentiality.normal,
        storage_path=storage_path,
        ingestion_status=IngestionStatus.uploaded,
        uploaded_by_id=uploaded_by_id,
    )
    session.add(document)
    session.flush()
    session.add(IngestionJob(document_id=document.id, status=IngestionJobStatus.queued))
    session.flush()
    return document


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


def mark_superseded(session: Session, *, older: Document, newer: Document) -> None:
    """Close the chain link: `older` is now superseded by `newer`. `older.status` is left
    untouched (Phase 0.3 decision; status transitions belong to Phase 3.2)."""
    older.superseded_by_document_id = newer.id
    session.flush()
