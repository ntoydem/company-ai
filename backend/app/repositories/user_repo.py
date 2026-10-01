import uuid
from collections.abc import Iterable

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.user import User, UserRole
from app.models.user_department import UserDepartment
from app.repositories import department_repo

DIRECTORY_LIMIT = 200


class PrimaryDepartmentNotAMembershipError(ValueError):
    """B-09: the primary department must be one of the user's memberships."""


def get_by_username(session: Session, username: str) -> User | None:
    return session.scalar(select(User).where(User.username == username))


def get_by_id(session: Session, user_id: uuid.UUID) -> User | None:
    return session.get(User, user_id)


def list_all(session: Session) -> list[User]:
    return list(session.scalars(select(User).order_by(User.username)).all())


def _resolve_primary(
    user: User, requested: uuid.UUID | None, *, requested_given: bool
) -> uuid.UUID | None:
    """B-09 rule: a given primary must be a membership (else error); when not given, keep
    the current one if it is still a membership, otherwise fall back to the first membership
    (slug order) — or None when the user has no memberships (management/admin)."""
    member_ids = {d.id for d in user.departments}
    if requested_given and requested is not None:
        if requested not in member_ids:
            raise PrimaryDepartmentNotAMembershipError(str(requested))
        return requested
    if user.primary_department_id in member_ids:
        return user.primary_department_id
    first = sorted(user.departments, key=lambda d: d.slug)[:1]
    return first[0].id if first else None


def create(
    session: Session,
    *,
    username: str,
    password_hash: str,
    display_name: str,
    role: UserRole,
    department_ids: Iterable[uuid.UUID] | None = None,
    title: str | None = None,
    primary_department_id: uuid.UUID | None = None,
) -> User:
    user = User(
        username=username,
        password_hash=password_hash,
        display_name=display_name,
        role=role,
        title=title,
    )
    if department_ids is not None:
        user.departments = department_repo.get_many_by_ids(session, department_ids)
    user.primary_department_id = _resolve_primary(
        user, primary_department_id, requested_given=primary_department_id is not None
    )
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
    title: str | None = None,
    primary_department_id: uuid.UUID | None = None,
    primary_department_given: bool = False,
) -> User:
    """Password reset is out of scope for Phase 5.2 (SORU 2, docs/plans/PHASE_5_2_PLAN.md)
    — no `password_hash` parameter here. `primary_department_given` distinguishes "not in
    the request" from an explicit null (the latter is only valid without memberships)."""
    if display_name is not None:
        user.display_name = display_name
    if role is not None:
        user.role = role
    if is_active is not None:
        user.is_active = is_active
    if title is not None:
        user.title = title
    if department_ids is not None:
        user.departments = department_repo.get_many_by_ids(session, department_ids)
    user.primary_department_id = _resolve_primary(
        user, primary_department_id, requested_given=primary_department_given
    )
    session.flush()
    return user


def search_directory(session: Session, *, q: str | None, department_slug: str | None) -> list[User]:
    """B-05: active users only; `q` matches display name or title; `department_slug`
    filters by *membership* ("who is in Finans"), not by primary department."""
    stmt = select(User).where(User.is_active.is_(True)).order_by(User.display_name, User.username)
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(or_(User.display_name.ilike(pattern), User.title.ilike(pattern)))
    if department_slug:
        stmt = stmt.where(
            User.id.in_(
                select(UserDepartment.user_id)
                .join(Department, Department.id == UserDepartment.department_id)
                .where(Department.slug == department_slug)
            )
        )
    return list(session.scalars(stmt.limit(DIRECTORY_LIMIT)).all())
