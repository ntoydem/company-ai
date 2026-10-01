"""`GET /api/directory` (B-05, Aşama C) — the narrow, everyone-can-read people list. Nothing
else from `users` is exposed here: no username, role, activity flag or hash."""

import uuid

from pydantic import BaseModel, ConfigDict


class DirectoryPerson(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    display_name: str
    title: str | None
    # The person's primary department (B-09); null for management/admin.
    department_slug: str | None
    department_name: str | None
