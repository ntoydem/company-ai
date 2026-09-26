import uuid
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.department import Department


def create(
    session: Session, *, name: str, slug: str, parent_id: uuid.UUID | None = None
) -> Department:
    department = Department(name=name, slug=slug, parent_id=parent_id)
    session.add(department)
    session.flush()
    return department


def get_by_slug(session: Session, slug: str) -> Department | None:
    return session.scalar(select(Department).where(Department.slug == slug))


def list_all(session: Session) -> list[Department]:
    return list(session.scalars(select(Department).order_by(Department.name)).all())


def get_many_by_ids(session: Session, ids: Iterable[uuid.UUID]) -> list[Department]:
    id_list = list(ids)
    if not id_list:
        return []
    return list(session.scalars(select(Department).where(Department.id.in_(id_list))).all())


def all_exist(session: Session, ids: Iterable[uuid.UUID]) -> bool:
    """Shared by `projects.py` and `users.py` (Phase 5.2) so both routers validate
    `department_ids` the same way instead of duplicating the check."""
    id_list = list(ids)
    if not id_list:
        return True
    return len(get_many_by_ids(session, id_list)) == len(set(id_list))
