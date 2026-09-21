"""Idempotent initial admin user (username/password from the environment)."""

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.user import UserRole
from app.repositories import user_repo
from app.services.security import hash_password

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class AdminSeedResult:
    username: str
    created: bool


def ensure_admin_user(session: Session, settings: Settings) -> AdminSeedResult:
    """Create the admin user if missing. Existing users are never modified (no password reset)."""
    existing = user_repo.get_by_username(session, settings.admin_username)
    if existing is not None:
        log.info("admin user exists, unchanged", extra={"username": existing.username})
        return AdminSeedResult(username=existing.username, created=False)

    user = user_repo.create(
        session,
        username=settings.admin_username,
        password_hash=hash_password(settings.admin_password.get_secret_value()),
        display_name="Yönetici",
        role=UserRole.admin,
    )
    session.commit()
    log.info("admin user created", extra={"username": user.username})
    return AdminSeedResult(username=user.username, created=True)
