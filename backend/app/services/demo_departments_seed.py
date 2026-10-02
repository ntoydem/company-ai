"""Idempotent demo departments + memberships (SPEC_02 §5/§8). Mirrors `admin_seed.py`.

Tree (product owner's mind map, Aşama C / B-20): Proje Finans, Mali İşler (+ Muhasebe,
Finansal Muhasebe), Hukuk, İdari İşler, İK, Enerji (+ Proje Geliştirme, O&M, EPC,
Üretim/Piyasa). Slugs are fixed — documents, ledger, eval and project links key on them;
only names changed. `enerji` is a member of the top-level `enerji_grubu` node only — its
children are covered too because their documents carry `department="enerji_grubu"` (the
subdepartment is a display/filter field, not an authorization unit — see
docs/plans/PHASE_1_2_PLAN.md T7). `yonetim` (management) gets no membership rows —
management sees every department regardless of membership (SPEC_02 §5).

This seed only creates what is missing. Corrections to an existing database (renames, the
`finans` user's dropped `mali_isler` membership) are migration 0010's job, so a fresh
install and an upgraded one end with the same tree.
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
    ("enerji_grubu", "Enerji", None),
    ("enerji_gelistirme", "Proje Geliştirme", "enerji_grubu"),
    ("enerji_epc_insaat", "EPC (İnşaat)", "enerji_grubu"),
    ("enerji_bakim", "O&M (İşletme ve Bakım)", "enerji_grubu"),
    ("enerji_uretim_piyasa", "Üretim/Piyasa", "enerji_grubu"),
    ("finans", "Proje Finans", None),
    ("hukuk", "Hukuk", None),
    ("mali_isler", "Mali İşler", None),
    ("mali_isler_muhasebe", "Muhasebe", "mali_isler"),
    ("mali_isler_finansal_muhasebe", "Finansal Muhasebe", "mali_isler"),
    ("idari_isler", "İdari İşler", None),
    ("ik", "İK", None),
)

# demo username -> department slugs it belongs to. `finans` is Proje Finans only since
# Aşama C (B-20/5, P-5: one person, one home); Phase 1.2 had given it `mali_isler` too.
_DEMO_USER_DEPARTMENTS: dict[str, tuple[str, ...]] = {
    "finans": ("finans",),
    "finans_mudur": ("finans",),  # B-08: the department manager is a member like anyone else
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
        session.flush()
        session.expire(user, ["departments"])
        # B-09: a fresh install sets the home department here (migration 0010's backfill
        # ran on an empty table); an existing primary is never changed.
        if user.primary_department_id is None and user.departments:
            user.primary_department_id = sorted(user.departments, key=lambda d: d.slug)[0].id
    session.commit()
    return results
