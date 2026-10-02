"""`tag_catalog` persistence (B-28b)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tag_catalog import TagCatalog, TagKind


def list_all(session: Session, *, active_only: bool = False) -> list[TagCatalog]:
    stmt = select(TagCatalog).order_by(TagCatalog.kind, TagCatalog.slug)
    if active_only:
        stmt = stmt.where(TagCatalog.is_active.is_(True))
    return list(session.scalars(stmt).all())


def active_slugs(session: Session) -> set[str]:
    return {t.slug for t in list_all(session, active_only=True)}


def get(session: Session, slug: str) -> TagCatalog | None:
    return session.get(TagCatalog, slug)


def create(
    session: Session,
    *,
    slug: str,
    label: str,
    kind: TagKind,
    created_by_id: uuid.UUID | None,
) -> TagCatalog:
    tag = TagCatalog(slug=slug, label=label, kind=kind, created_by_id=created_by_id)
    session.add(tag)
    session.flush()
    return tag


def unknown_tags(session: Session, tags: list[str]) -> list[str]:
    """Tags not in the *active* catalogue (strict rule, BACKEND_GAPS §4.7.4 / Naci SORU 1)."""
    allowed = active_slugs(session)
    return sorted({t for t in tags if t not in allowed})
