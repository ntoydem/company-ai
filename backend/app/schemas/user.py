import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.user import UserRole


class UserCreateRequest(BaseModel):
    username: str
    password: str
    display_name: str
    role: UserRole = UserRole.employee
    department_ids: list[uuid.UUID] = Field(default_factory=list)


class UserUpdateRequest(BaseModel):
    """Password reset is out of scope (Phase 5.2 SORU 2) — no `password` field here.
    `username` is immutable after creation, same discipline as `Project.code`."""

    display_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    department_ids: list[uuid.UUID] | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    display_name: str
    role: UserRole
    is_active: bool
    department_ids: list[uuid.UUID]
    department_slugs: list[str]
