import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, UserRole


def get_by_username(session: Session, username: str) -> User | None:
    return session.scalar(select(User).where(User.username == username))


def get_by_id(session: Session, user_id: uuid.UUID) -> User | None:
    return session.get(User, user_id)


def create(
    session: Session,
    *,
    username: str,
    password_hash: str,
    display_name: str,
    role: UserRole,
) -> User:
    user = User(
        username=username,
        password_hash=password_hash,
        display_name=display_name,
        role=role,
    )
    session.add(user)
    session.flush()
    return user
