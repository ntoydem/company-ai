"""Idempotent demo departments + memberships (SPEC_02 §5/§8). Mirrors `admin_seed.py`.

Tree: Enerji Grubu (+ Geliştirme/EPC-İnşaat/Bakım), Finans, Hukuk, Mali İşler, İdari
İşler. `enerji` is a member of the top-level `enerji_grubu` node only — its three
children are covered too because their documents also carry `department="enerji_grubu"`
(the subdepartment is a display/filter field, not an authorization unit — see
docs/plans/PHASE_1_2_PLAN.md T7). `yonetim` (management) gets no membership rows —
management sees every department regardless of membership (SPEC_02 §5).
"""

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.user_department import UserDepartment
from app.repositories import department_repo, user_repo

log = logging.getLogger(__name__)

# (slug, name, parent_slug) — parents listed before children.
_DEPARTMENTS: tuple[tuple[str, str, str | None], ...] = (
    ("enerji_grubu", "Enerji Grubu", None),
    ("enerji_gelistirme", "Geliştirme", "enerji_grubu"),
    ("enerji_epc_insaat", "EPC-İnşaat", "enerji_grubu"),
    ("enerji_bakim", "Bakım", "enerji_grubu"),
    ("finans", "Finans", None),
    ("hukuk", "Hukuk", None),
    ("mali_isler", "Mali İşler", None),
    ("idari_isler", "İdari İşler", None),
)

# demo username -> department slugs it belongs to (SORU 1 cevabı, PHASE_1_2_PLAN.md).
_DEMO_USER_DEPARTMENTS: dict[str, tuple[str, ...]] = {
    "finans": ("finans", "mali_isler"),
    "hukuk": ("hukuk",),
    "enerji": ("enerji_grubu",),
}


@dataclass(frozen=True)
class DemoSeedResult:
    slug: str
    created: bool


def ensure_demo_departments(session: Session, settings: Settings) -> list[DemoSeedResult]:
    """Create each department if missing. Existing rows are never modified."""
    results = []
    for slug, name, parent_slug in _DEPARTMENTS:
        existing = department_repo.get_by_slug(session, slug)
        if existing is not None:
            log.info("department exists, unchanged", extra={"slug": existing.slug})
            results.append(DemoSeedResult(slug=existing.slug, created=False))
            continue
        parent = department_repo.get_by_slug(session, parent_slug) if parent_slug else None
        department = department_repo.create(
            session, name=name, slug=slug, parent_id=parent.id if parent else None
        )
        log.info("department created", extra={"slug": department.slug})
        results.append(DemoSeedResult(slug=department.slug, created=True))
    session.commit()
    return results


def ensure_demo_department_memberships(
    session: Session, settings: Settings
) -> list[DemoSeedResult]:
    """Attach each demo user to its department(s) if not already a member."""
    results = []
    for username, slugs in _DEMO_USER_DEPARTMENTS.items():
        user = user_repo.get_by_username(session, username)
        if user is None:
            log.warning("demo user missing, skipping membership", extra={"username": username})
            continue
        for slug in slugs:
            department = department_repo.get_by_slug(session, slug)
            if department is None:
                log.warning("demo department missing, skipping membership", extra={"slug": slug})
                continue
            label = f"{username}:{slug}"
            existing = session.get(UserDepartment, (user.id, department.id))
            if existing is not None:
                log.info("membership exists, unchanged", extra={"membership": label})
                results.append(DemoSeedResult(slug=label, created=False))
                continue
            session.add(UserDepartment(user_id=user.id, department_id=department.id))
            log.info("membership created", extra={"membership": label})
            results.append(DemoSeedResult(slug=label, created=True))
    session.commit()
    return results
