"""Shared department/membership builders for tests (Phase 1.2). Mirrors `t0_fixtures.py`."""

from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.user import User
from app.models.user_department import UserDepartment


def make_department(
    session: Session, *, slug: str, name: str | None = None, parent: Department | None = None
) -> Department:
    department = Department(name=name or slug, slug=slug, parent_id=parent.id if parent else None)
    session.add(department)
    session.commit()
    return department


def add_user_to_department(session: Session, user: User, department: Department) -> None:
    session.add(UserDepartment(user_id=user.id, department_id=department.id))
    session.commit()
    session.expire(user, ["departments"])
