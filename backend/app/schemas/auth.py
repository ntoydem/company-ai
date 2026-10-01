from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from app.models.company_settings import ProductLevel
from app.models.user import User, UserRole


class LoginRequest(BaseModel):
    username: str
    password: str


class CurrentUserResponse(BaseModel):
    """Returned by both `POST /api/auth/login` and `GET /api/auth/me`. `enabled_products`
    (B-25) is company-wide state, not a user attribute, so it is not `from_attributes`
    on the user row — see `from_user`."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    display_name: str
    role: UserRole
    department_slugs: list[str]
    enabled_products: list[ProductLevel]
    # Aşama C: B-09 home department (also first in `department_slugs`) and B-05 title.
    primary_department_slug: str | None
    title: str | None

    @classmethod
    def from_user(cls, user: User, enabled_products: list[ProductLevel]) -> CurrentUserResponse:
        return cls(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            role=user.role,
            department_slugs=user.department_slugs,
            enabled_products=enabled_products,
            primary_department_slug=user.primary_department_slug,
            title=user.title,
        )
