import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.project import ProjectStage


class ProjectCreateRequest(BaseModel):
    name: str
    code: str
    stage: ProjectStage = ProjectStage.development
    department_ids: list[uuid.UUID] = Field(default_factory=list)


class ProjectUpdateRequest(BaseModel):
    name: str | None = None
    stage: ProjectStage | None = None
    is_active: bool | None = None
    department_ids: list[uuid.UUID] | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    stage: ProjectStage
    is_active: bool
    department_ids: list[uuid.UUID]
