"""`document_metadata_suggestions` persistence (SPEC_02 §4, Phase 3.2)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document_metadata_suggestion import DocumentMetadataSuggestion, SuggestionStatus


def get_by_document_id(
    session: Session, document_id: uuid.UUID
) -> DocumentMetadataSuggestion | None:
    return session.scalar(
        select(DocumentMetadataSuggestion).where(
            DocumentMetadataSuggestion.document_id == document_id
        )
    )


def upsert(
    session: Session,
    *,
    document_id: uuid.UUID,
    model: str,
    status: SuggestionStatus,
    fields: dict[str, Any],
    error: str | None = None,
) -> DocumentMetadataSuggestion:
    """One row per document (unique `document_id`). A fresh generation (first attempt, or
    a retry of a `failed`/`rejected` one) overwrites the existing row in place rather than
    inserting a new one — V0 keeps no suggestion history."""
    suggestion = get_by_document_id(session, document_id)
    if suggestion is None:
        suggestion = DocumentMetadataSuggestion(document_id=document_id)
        session.add(suggestion)
    suggestion.model = model
    suggestion.status = status
    suggestion.fields = fields
    suggestion.error = error
    suggestion.applied_at = None
    suggestion.applied_by_id = None
    session.flush()
    return suggestion


def mark_applied(
    session: Session, suggestion: DocumentMetadataSuggestion, *, applied_by_id: uuid.UUID
) -> None:
    suggestion.status = SuggestionStatus.applied
    suggestion.applied_at = datetime.now(UTC)
    suggestion.applied_by_id = applied_by_id
    session.flush()


def mark_rejected(session: Session, suggestion: DocumentMetadataSuggestion) -> None:
    suggestion.status = SuggestionStatus.rejected
    session.flush()
