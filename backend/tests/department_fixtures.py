"""Shared department/membership builders for tests (Phase 1.2). Mirrors `t0_fixtures.py`."""

from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.user import User, UserRole
from app.models.user_department import UserDepartment
from app.repositories import user_repo
from app.services.security import hash_password


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


def make_department_manager(
    session: Session, department: Department, username: str | None = None
) -> User:
    """B-28: a department needs a `department_manager` member before anyone else may upload
    into it (409 `approver_not_configured` otherwise) — the approver of its documents."""
    user = user_repo.create(
        session,
        username=username or f"{department.slug}-mudur",
        password_hash=hash_password("gecerli-sifre"),
        display_name=f"{department.slug} müdür",
        role=UserRole.department_manager,
    )
    add_user_to_department(session, user, department)
    return user
