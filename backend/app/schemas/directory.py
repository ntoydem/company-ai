"""`GET /api/directory` (B-05, Aşama C) — the narrow, everyone-can-read people list. Nothing
else from `users` is exposed here: no username, role, activity flag or hash."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from app.models.user import User


class DirectoryPerson(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    display_name: str
    title: str | None
    # The person's primary department (B-09); null for management/admin.
    department_slug: str | None
    department_name: str | None

    @classmethod
    def from_user(cls, user: User) -> DirectoryPerson:
        return cls(
            id=user.id,
            display_name=user.display_name,
            title=user.title,
            department_slug=user.primary_department_slug,
            department_name=user.primary_department.name if user.primary_department else None,
        )
