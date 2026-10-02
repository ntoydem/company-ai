"""`admin_events` — append-only (B-28b, ADR-025)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin_event import AdminEvent
from app.models.user import User

EVENTS_LIMIT_MAX = 500


def add(
    session: Session,
    *,
    actor: User,
    kind: str,
    target: str,
    before: object = None,
    after: object = None,
) -> AdminEvent:
    event = AdminEvent(
        actor_user_id=actor.id,
        actor_name=actor.display_name,
        kind=kind,
        target=target,
        before=None if before is None else str(before),
        after=None if after is None else str(after),
    )
    session.add(event)
    session.flush()
    return event


def list_events(session: Session, *, limit: int = 100, kind: str | None = None) -> list[AdminEvent]:
    stmt = select(AdminEvent).order_by(AdminEvent.created_at.desc(), AdminEvent.id)
    if kind is not None:
        stmt = stmt.where(AdminEvent.kind == kind)
    return list(session.scalars(stmt.limit(min(limit, EVENTS_LIMIT_MAX))).all())
