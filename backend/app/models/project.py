import enum
import uuid

from sqlalchemy import Boolean, Enum, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.department import Department


class ProjectStage(enum.StrEnum):
    development = "development"
    construction = "construction"
    operation = "operation"


class Project(TimestampMixin, Base):
    """Not hard-coded (SPEC_02 §6); admin CRUD. A project may span several departments,
    but a document's permission always comes from its own `department`, never from its
    project (ADR-004) — `departments` here is organisational/filtering only."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    stage: Mapped[ProjectStage] = mapped_column(
        Enum(ProjectStage, name="project_stage", values_callable=lambda e: [m.value for m in e]),
        default=ProjectStage.development,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    departments: Mapped[list[Department]] = relationship(
        "Department", secondary="project_departments"
    )

    @property
    def department_ids(self) -> list[uuid.UUID]:
        return [department.id for department in self.departments]

    def __repr__(self) -> str:
        return f"Project(code={self.code!r})"
