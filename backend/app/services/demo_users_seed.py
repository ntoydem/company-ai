"""Idempotent demo users (SPEC_02 §5). Mirrors `admin_seed.py`.

Phase 1.1 seeds only `role` — department membership (`user_departments`, Phase 1.2)
does not exist yet, so `finans`/`hukuk`/`enerji` are plain `employee` accounts for now.
"""

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.user import UserRole
from app.repositories import user_repo
from app.services.security import hash_password

log = logging.getLogger(__name__)

_DEMO_USERS: tuple[tuple[str, str, UserRole], ...] = (
    ("yonetim", "Yönetim", UserRole.management),
    ("finans", "Finans", UserRole.employee),
    ("hukuk", "Hukuk", UserRole.employee),
    ("enerji", "Enerji", UserRole.employee),
)


@dataclass(frozen=True)
class DemoSeedResult:
    username: str
    created: bool


def ensure_demo_users(session: Session, settings: Settings) -> list[DemoSeedResult]:
    """Create each demo user if missing. Existing users are never modified."""
    password_hash = hash_password(settings.demo_user_password.get_secret_value())
    results = []
    for username, display_name, role in _DEMO_USERS:
        existing = user_repo.get_by_username(session, username)
        if existing is not None:
            log.info("demo user exists, unchanged", extra={"username": existing.username})
            results.append(DemoSeedResult(username=existing.username, created=False))
            continue
        user = user_repo.create(
            session,
            username=username,
            password_hash=password_hash,
            display_name=display_name,
            role=role,
        )
        log.info("demo user created", extra={"username": user.username})
        results.append(DemoSeedResult(username=user.username, created=True))
    session.commit()
    return results
