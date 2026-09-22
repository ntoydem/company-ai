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
