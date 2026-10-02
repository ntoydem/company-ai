"""Document-type guide (B-28b, BACKEND_GAPS §4.7.2, ADR-025): per-company, admin-edited,
a guide — not a form. Everyone reads the active families (upload screen); the customer admin
edits them. `/signals` surfaces the §4.7.3 hint: which keys staff keep adding by hand."""

import json
from collections import Counter
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.db import get_session
from app.models.document import Document
from app.models.document_review_event import DocumentReviewEvent, ReviewEventKind
from app.models.document_type_guide import DocumentTypeGuide
from app.models.user import User
from app.repositories import admin_event_repo, guide_repo
from app.schemas.catalog import (
    AdminEventResponse,
    GuideCreateRequest,
    GuideResponse,
    GuideSignal,
    GuideUpdateRequest,
)
from app.services import type_family

router = APIRouter(prefix="/api/document-type-guide", tags=["guide"])
admin_router = APIRouter(prefix="/api/admin/document-type-guide", tags=["guide"])
events_router = APIRouter(prefix="/api/admin/events", tags=["guide"])

FAMILY_EXISTS_MESSAGE = "Bu aile zaten tanımlı."
FAMILY_NOT_FOUND_MESSAGE = "Aile bulunamadı."


@router.get("", response_model=list[GuideResponse])
def list_active_guide(
    session: Annotated[Session, Depends(get_session)],
    _user: Annotated[User, Depends(get_current_user)],
) -> list[GuideResponse]:
    return [GuideResponse.model_validate(g) for g in guide_repo.list_all(session, active_only=True)]


@admin_router.get("", response_model=list[GuideResponse])
def list_guide(
    session: Annotated[Session, Depends(get_session)],
    _admin: Annotated[User, Depends(require_admin)],
) -> list[GuideResponse]:
    return [GuideResponse.model_validate(g) for g in guide_repo.list_all(session)]


@admin_router.post("", response_model=GuideResponse, status_code=201)
def create_family(
    body: GuideCreateRequest,
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[User, Depends(require_admin)],
) -> GuideResponse:
    if guide_repo.get(session, body.family) is not None:
        raise HTTPException(409, FAMILY_EXISTS_MESSAGE)
    guide = DocumentTypeGuide(
        family=body.family,
        label=body.label,
        type_patterns=[type_family.fold(p.strip()) for p in body.type_patterns if p.strip()],
        suggested_extra_fields=[f.model_dump() for f in body.suggested_extra_fields],
        suggested_tags=body.suggested_tags,
        standard_fields_emphasis=body.standard_fields_emphasis,
        prompt_hint=body.prompt_hint,
    )
    session.add(guide)
    session.flush()
    admin_event_repo.add(
        session, actor=admin, kind="guide_created", target=body.family, after=body.label
    )
    session.commit()
    return GuideResponse.model_validate(guide)


@admin_router.patch("/{family}", response_model=GuideResponse)
def update_family(
    family: str,
    body: GuideUpdateRequest,
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[User, Depends(require_admin)],
) -> GuideResponse:
    guide = guide_repo.get(session, family)
    if guide is None:
        raise HTTPException(404, FAMILY_NOT_FOUND_MESSAGE)
    before = json.dumps(guide_repo.as_dicts([guide])[0], ensure_ascii=False, sort_keys=True)
    if body.label is not None:
        guide.label = body.label
    if body.type_patterns is not None:
        guide.type_patterns = [type_family.fold(p.strip()) for p in body.type_patterns if p.strip()]
    if body.suggested_extra_fields is not None:
        guide.suggested_extra_fields = [f.model_dump() for f in body.suggested_extra_fields]
    if body.suggested_tags is not None:
        guide.suggested_tags = body.suggested_tags
    if body.standard_fields_emphasis is not None:
        guide.standard_fields_emphasis = body.standard_fields_emphasis
    if body.prompt_hint is not None:
        guide.prompt_hint = body.prompt_hint
    if body.is_active is not None:
        guide.is_active = body.is_active
    session.flush()
    after = json.dumps(guide_repo.as_dicts([guide])[0], ensure_ascii=False, sort_keys=True)
    if after != before:
        admin_event_repo.add(
            session, actor=admin, kind="guide_updated", target=family, before=before, after=after
        )
    session.commit()
    return GuideResponse.model_validate(guide)


@admin_router.get("/signals", response_model=list[GuideSignal])
def guide_signals(
    session: Annotated[Session, Depends(get_session)],
    _admin: Annotated[User, Depends(require_admin)],
) -> list[GuideSignal]:
    """`field_added` events grouped by (family of the document's type, key) — the human reads
    this and decides whether the guide should suggest that key; nothing changes by itself."""
    guides = guide_repo.as_dicts(guide_repo.list_all(session, active_only=True))
    rows = session.execute(
        select(DocumentReviewEvent.field, Document.document_type)
        .join(Document, Document.id == DocumentReviewEvent.document_id)
        .where(DocumentReviewEvent.kind == ReviewEventKind.field_added)
    ).all()
    counter: Counter[tuple[str, str]] = Counter()
    for field, document_type in rows:
        if not field or not field.startswith(type_family.EXTRA_PREFIX_LITERAL):
            continue
        key = field[len(type_family.EXTRA_PREFIX_LITERAL) :]
        counter[(type_family.match_family(document_type, guides), key)] += 1
    return [
        GuideSignal(family=family, key=key, count=count)
        for (family, key), count in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    ]


@events_router.get("", response_model=list[AdminEventResponse])
def list_admin_events(
    session: Annotated[Session, Depends(get_session)],
    _admin: Annotated[User, Depends(require_admin)],
    kind: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[AdminEventResponse]:
    return [
        AdminEventResponse.model_validate(e)
        for e in admin_event_repo.list_events(session, limit=limit, kind=kind)
    ]
