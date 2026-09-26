import uuid
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.repositories import department_repo


def get_by_username(session: Session, username: str) -> User | None:
    return session.scalar(select(User).where(User.username == username))


def get_by_id(session: Session, user_id: uuid.UUID) -> User | None:
    return session.get(User, user_id)


def list_all(session: Session) -> list[User]:
    return list(session.scalars(select(User).order_by(User.username)).all())


def create(
    session: Session,
    *,
    username: str,
    password_hash: str,
    display_name: str,
    role: UserRole,
    department_ids: Iterable[uuid.UUID] | None = None,
) -> User:
    user = User(
        username=username,
        password_hash=password_hash,
        display_name=display_name,
        role=role,
    )
    if department_ids is not None:
        user.departments = department_repo.get_many_by_ids(session, department_ids)
    session.add(user)
    session.flush()
    return user


def update(
    session: Session,
    user: User,
    *,
    display_name: str | None = None,
    role: UserRole | None = None,
    is_active: bool | None = None,
    department_ids: Iterable[uuid.UUID] | None = None,
) -> User:
    """Password reset is out of scope for Phase 5.2 (SORU 2, docs/plans/PHASE_5_2_PLAN.md)
    — no `password_hash` parameter here."""
    if display_name is not None:
        user.display_name = display_name
    if role is not None:
        user.role = role
    if is_active is not None:
        user.is_active = is_active
    if department_ids is not None:
        user.departments = department_repo.get_many_by_ids(session, department_ids)
    session.flush()
    return user
