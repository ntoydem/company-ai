"""Idempotent demo projects (SPEC_02 §6). Mirrors `admin_seed.py`/`demo_users_seed.py`.

Ankara RES (operation) and İzmir RES (development) — linked to `enerji_grubu`, `finans`
and `hukuk` (SORU 4 cevabı, docs/plans/PHASE_1_2_PLAN.md); `mali_isler`/`idari_isler`
are company-wide, not project-specific. This linkage is organisational/filtering only —
a document's permission always comes from its own `department`, never from its project
(ADR-004).
"""

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.project import ProjectStage
from app.repositories import department_repo, project_repo

log = logging.getLogger(__name__)

_DEMO_PROJECTS: tuple[tuple[str, str, ProjectStage, tuple[str, ...]], ...] = (
    ("ANK_RES", "Ankara RES", ProjectStage.operation, ("enerji_grubu", "finans", "hukuk")),
    ("IZM_RES", "İzmir RES", ProjectStage.development, ("enerji_grubu", "finans", "hukuk")),
)


@dataclass(frozen=True)
class DemoSeedResult:
    code: str
    created: bool


def ensure_demo_projects(session: Session, settings: Settings) -> list[DemoSeedResult]:
    """Create each project if missing. Existing rows are never modified."""
    results = []
    for code, name, stage, department_slugs in _DEMO_PROJECTS:
        existing = project_repo.get_by_code(session, code)
        if existing is not None:
            log.info("project exists, unchanged", extra={"code": existing.code})
            results.append(DemoSeedResult(code=existing.code, created=False))
            continue
        departments = [
            department
            for slug in department_slugs
            if (department := department_repo.get_by_slug(session, slug)) is not None
        ]
        project = project_repo.create(
            session,
            name=name,
            code=code,
            stage=stage,
            department_ids=[department.id for department in departments],
        )
        log.info("project created", extra={"code": project.code})
        results.append(DemoSeedResult(code=project.code, created=True))
    session.commit()
    return results
