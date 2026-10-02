"""`document_review_events` persistence (B-28, ADR-024) — append-only."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document_review_event import DocumentReviewEvent, ReviewEventKind
from app.models.user import User


def add_event(
    session: Session,
    *,
    document_id: uuid.UUID,
    actor: User,
    kind: ReviewEventKind,
    field: str | None = None,
    before: object = None,
    after: object = None,
    confidence: float | None = None,
    comment: str | None = None,
) -> DocumentReviewEvent:
    event = DocumentReviewEvent(
        document_id=document_id,
        actor_user_id=actor.id,
        actor_name=actor.display_name,
        kind=kind,
        field=field,
        before=None if before is None else str(before),
        after=None if after is None else str(after),
        confidence=confidence,
        comment=comment,
    )
    session.add(event)
    session.flush()
    return event


def list_events(session: Session, document_id: uuid.UUID) -> list[DocumentReviewEvent]:
    stmt = (
        select(DocumentReviewEvent)
        .where(DocumentReviewEvent.document_id == document_id)
        .order_by(DocumentReviewEvent.created_at, DocumentReviewEvent.id)
    )
    return list(session.scalars(stmt).all())
