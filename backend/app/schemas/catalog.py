"""Tag catalogue, document-type guide and admin-event schemas (B-28b, ADR-025)."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.tag_catalog import TagKind


class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    label: str
    kind: TagKind
    is_active: bool


class TagCreateRequest(BaseModel):
    slug: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=128)
    kind: TagKind = TagKind.identity


class TagUpdateRequest(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=128)
    kind: TagKind | None = None
    is_active: bool | None = None


class GuideField(BaseModel):
    key: str = Field(min_length=1, max_length=48)
    label: str = Field(default="", max_length=128)
    hint: str = Field(default="", max_length=256)


class GuideResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    family: str
    label: str
    type_patterns: list[str]
    suggested_extra_fields: list[dict[str, Any]]
    suggested_tags: list[str]
    standard_fields_emphasis: list[str]
    prompt_hint: str
    is_active: bool


class GuideCreateRequest(BaseModel):
    family: str = Field(min_length=1, max_length=32, pattern=r"^[a-z][a-z0-9_]*$")
    label: str = Field(min_length=1, max_length=128)
    type_patterns: list[str] = Field(default_factory=list)
    suggested_extra_fields: list[GuideField] = Field(default_factory=list)
    suggested_tags: list[str] = Field(default_factory=list)
    standard_fields_emphasis: list[str] = Field(default_factory=list)
    prompt_hint: str = Field(default="", max_length=500)


class GuideUpdateRequest(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=128)
    type_patterns: list[str] | None = None
    suggested_extra_fields: list[GuideField] | None = None
    suggested_tags: list[str] | None = None
    standard_fields_emphasis: list[str] | None = None
    prompt_hint: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class GuideSignal(BaseModel):
    """§4.7.3: staff keep adding this key by hand in this family — a hint for the guide."""

    family: str
    key: str
    count: int


class AdminEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    actor_name: str
    kind: str
    target: str
    before: str | None
    after: str | None
