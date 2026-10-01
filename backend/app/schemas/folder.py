"""Folder API shapes (B-26, Aşama E) — field names match AI-BalBal `proposed.ts` §10
(`AdminFolder`, `FolderGrant`, `UserFolder`, `FolderAuditEntry`) exactly."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.folder import FolderAccess

GrantChoice = Literal["none", "read", "write"]


class FolderGrantResponse(BaseModel):
    department_slug: str
    access: FolderAccess
    # true = inherited from an ancestor folder; false = defined on this folder.
    inherited: bool


class AdminFolderResponse(BaseModel):
    id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None
    owner_department_slug: str
    grants: list[FolderGrantResponse]
    document_count: int


class FolderCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    parent_id: uuid.UUID | None = None
    owner_department_slug: str


class FolderUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    parent_id: uuid.UUID | None = None


class FolderGrantChoice(BaseModel):
    department_slug: str
    access: GrantChoice


class FolderGrantsUpdateRequest(BaseModel):
    grants: list[FolderGrantChoice]


class FolderAuditEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    actor_name: str
    folder_id: uuid.UUID | None
    folder_name: str
    department_slug: str
    before: GrantChoice
    after: GrantChoice


class UserFolderResponse(BaseModel):
    id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None
    owner_department_slug: str
    access: FolderAccess
    document_count: int
