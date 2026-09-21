from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuthorizationScope(BaseModel):
    """Optional narrowing of a query (department screen, project filter).

    Scope only ever *restricts* the allowed set; it never grants access.
    """

    model_config = ConfigDict(frozen=True)

    department: str | None = None
    project_id: UUID | None = None
