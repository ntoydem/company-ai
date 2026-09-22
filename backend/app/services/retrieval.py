"""`retrieve()`: authorize first (ADR-004), then full-text search (ADR-007)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User
from app.repositories.document_chunk_repo import RetrievedChunk, search_fts
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.authorization import AuthorizationScope
from app.schemas.retrieval import RetrievalFilters
from app.services.authorization import allowed_document_ids


def retrieve(
    session: Session, user: User, question: str, filters: RetrievalFilters
) -> list[RetrievedChunk]:
    scope = AuthorizationScope(department=filters.department, project_id=filters.project_id)
    provider = SqlDocumentIdsProvider(session)
    allowed = allowed_document_ids(user, scope, provider)
    if not allowed:
        return []
    return search_fts(
        session, allowed_ids=allowed, query=question, top_k=get_settings().retrieval_top_k
    )
