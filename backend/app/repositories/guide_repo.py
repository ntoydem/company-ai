"""`document_type_guide` persistence (B-28b)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document_type_guide import DocumentTypeGuide


def list_all(session: Session, *, active_only: bool = False) -> list[DocumentTypeGuide]:
    stmt = select(DocumentTypeGuide).order_by(DocumentTypeGuide.family)
    if active_only:
        stmt = stmt.where(DocumentTypeGuide.is_active.is_(True))
    return list(session.scalars(stmt).all())


def get(session: Session, family: str) -> DocumentTypeGuide | None:
    return session.get(DocumentTypeGuide, family)


def as_dicts(guides: list[DocumentTypeGuide]) -> list[dict[str, Any]]:
    """Plain dicts for the pure matcher / prompt builder (`type_family.match_family`)."""
    return [
        {
            "family": g.family,
            "label": g.label,
            "type_patterns": list(g.type_patterns or []),
            "suggested_extra_fields": list(g.suggested_extra_fields or []),
            "suggested_tags": list(g.suggested_tags or []),
            "standard_fields_emphasis": list(g.standard_fields_emphasis or []),
            "prompt_hint": g.prompt_hint or "",
            "is_active": g.is_active,
        }
        for g in guides
    ]
