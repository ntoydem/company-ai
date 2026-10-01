import uuid
from collections.abc import Iterable

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStage
from app.repositories import department_repo


def create(
    session: Session,
    *,
    name: str,
    code: str,
    stage: ProjectStage,
    department_ids: Iterable[uuid.UUID],
) -> Project:
    project = Project(name=name, code=code, stage=stage)
    project.departments = department_repo.get_many_by_ids(session, department_ids)
    session.add(project)
    session.flush()
    return project


def get(session: Session, project_id: uuid.UUID) -> Project | None:
    return session.get(Project, project_id)


def get_by_code(session: Session, code: str) -> Project | None:
    return session.scalar(select(Project).where(Project.code == code))


def list_all(session: Session) -> list[Project]:
    return list(session.scalars(select(Project).order_by(Project.name)).all())


def search(session: Session, q: str) -> list[Project]:
    """B-14: name / code `ILIKE %q%`; same visibility as `GET /api/projects` (every
    signed-in user, inactive projects included — the UI shows `is_active`)."""
    pattern = f"%{q.strip()}%"
    stmt = (
        select(Project)
        .where(or_(Project.name.ilike(pattern), Project.code.ilike(pattern)))
        .order_by(Project.code)
    )
    return list(session.scalars(stmt).all())


def update(
    session: Session,
    project: Project,
    *,
    name: str | None = None,
    stage: ProjectStage | None = None,
    is_active: bool | None = None,
    department_ids: Iterable[uuid.UUID] | None = None,
) -> Project:
    if name is not None:
        project.name = name
    if stage is not None:
        project.stage = stage
    if is_active is not None:
        project.is_active = is_active
    if department_ids is not None:
        project.departments = department_repo.get_many_by_ids(session, department_ids)
    session.flush()
    return project
