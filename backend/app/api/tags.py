"""Tag catalogue (B-28b, BACKEND_GAPS §4.7.4, ADR-025). Everyone reads the active list; the
customer admin grows/retires it (`require_admin`). Tags are never deleted — older documents
reference them; `is_active=false` retires one. Every change is an `admin_events` row."""

import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.db import get_session
from app.models.user import User
from app.repositories import admin_event_repo, tag_repo
from app.schemas.catalog import TagCreateRequest, TagResponse, TagUpdateRequest

router = APIRouter(prefix="/api/tags", tags=["tags"])
admin_router = APIRouter(prefix="/api/admin/tags", tags=["tags"])

TAG_EXISTS_MESSAGE = "Bu etiket zaten katalogda."
TAG_NOT_FOUND_MESSAGE = "Etiket bulunamadı."
INVALID_SLUG_MESSAGE = (
    "Etiket adı küçük harf, rakam, tire ve alt çizgiden oluşmalı (örn. faiz-değişikliği)."
)
# Lower-case letters (Turkish included), digits, '-' and '_' — the §4.7.4 examples' shape.
_SLUG_RE = re.compile(r"^[a-z0-9çğıöşü][a-z0-9çğıöşü_-]{0,63}$")


@router.get("", response_model=list[TagResponse])
def list_active_tags(
    session: Annotated[Session, Depends(get_session)],
    _user: Annotated[User, Depends(get_current_user)],
) -> list[TagResponse]:
    return [TagResponse.model_validate(t) for t in tag_repo.list_all(session, active_only=True)]


@admin_router.get("", response_model=list[TagResponse])
def list_all_tags(
    session: Annotated[Session, Depends(get_session)],
    _admin: Annotated[User, Depends(require_admin)],
) -> list[TagResponse]:
    return [TagResponse.model_validate(t) for t in tag_repo.list_all(session)]


@admin_router.post("", response_model=TagResponse, status_code=201)
def create_tag(
    body: TagCreateRequest,
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[User, Depends(require_admin)],
) -> TagResponse:
    slug = body.slug.strip()
    if not _SLUG_RE.match(slug):
        raise HTTPException(422, INVALID_SLUG_MESSAGE)
    if tag_repo.get(session, slug) is not None:
        raise HTTPException(409, TAG_EXISTS_MESSAGE)
    tag = tag_repo.create(
        session, slug=slug, label=body.label.strip(), kind=body.kind, created_by_id=admin.id
    )
    admin_event_repo.add(
        session,
        actor=admin,
        kind="tag_created",
        target=slug,
        after=f"{body.kind.value}:{tag.label}",
    )
    session.commit()
    return TagResponse.model_validate(tag)


@admin_router.patch("/{slug}", response_model=TagResponse)
def update_tag(
    slug: str,
    body: TagUpdateRequest,
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[User, Depends(require_admin)],
) -> TagResponse:
    tag = tag_repo.get(session, slug)
    if tag is None:
        raise HTTPException(404, TAG_NOT_FOUND_MESSAGE)
    before = f"{tag.kind.value}:{tag.label}:{'active' if tag.is_active else 'inactive'}"
    if body.label is not None:
        tag.label = body.label.strip()
    if body.kind is not None:
        tag.kind = body.kind
    if body.is_active is not None:
        tag.is_active = body.is_active
    after = f"{tag.kind.value}:{tag.label}:{'active' if tag.is_active else 'inactive'}"
    if after != before:
        admin_event_repo.add(
            session, actor=admin, kind="tag_updated", target=slug, before=before, after=after
        )
    session.commit()
    return TagResponse.model_validate(tag)
