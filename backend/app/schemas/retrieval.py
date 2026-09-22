from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RetrievalFilters(BaseModel):
    """Optional narrowing passed to `retrieve()`; forwarded as an `AuthorizationScope`."""

    model_config = ConfigDict(frozen=True)

    department: str | None = None
    project_id: UUID | None = None
