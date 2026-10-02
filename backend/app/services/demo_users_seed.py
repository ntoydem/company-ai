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

# (username, display name, role, title) — titles are fictional/generic (P-9, Aşama C B-05).
_DEMO_USERS: tuple[tuple[str, str, UserRole, str], ...] = (
    ("yonetim", "Yönetim", UserRole.management, "Genel Müdür Yardımcısı"),
    ("finans", "Proje Finans", UserRole.employee, "Proje Finans Uzmanı"),
    ("hukuk", "Hukuk", UserRole.employee, "Hukuk Müşaviri"),
    ("enerji", "Enerji", UserRole.employee, "Enerji Grubu Uzmanı"),
    # B-08 (02.10.2026, Naci SORU 1a): the one demo manager — Proje Finans holds the only
    # `restricted` demo document (DOC-ANK-FIN-008), so the rule is visible live.
    ("finans_mudur", "Proje Finans Müdürü", UserRole.department_manager, "Proje Finans Müdürü"),
)


@dataclass(frozen=True)
class DemoSeedResult:
    username: str
    created: bool


def ensure_demo_users(session: Session, settings: Settings) -> list[DemoSeedResult]:
    """Create each demo user if missing. Existing users are never modified."""
    password_hash = hash_password(settings.demo_user_password.get_secret_value())
    results = []
    for username, display_name, role, title in _DEMO_USERS:
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
            title=title,
        )
        log.info("demo user created", extra={"username": user.username})
        results.append(DemoSeedResult(username=user.username, created=True))
    session.commit()
    return results
