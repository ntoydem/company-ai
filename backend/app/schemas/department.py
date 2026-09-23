import uuid

from pydantic import BaseModel, ConfigDict


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    parent_id: uuid.UUID | None
