"""Idempotent root folders (B-26, Aşama E): one per top-level department, named after it.
Mirrors migration 0011's data step for a fresh install. The richer demo tree (sub-folders,
cross-department grants) is B-18's job; the customer's admin builds the real one."""

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.repositories import department_repo, folder_repo

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DemoSeedResult:
    slug: str
    created: bool


def ensure_demo_root_folders(session: Session, settings: Settings) -> list[DemoSeedResult]:
    del settings
    results = []
    for department in department_repo.list_all(session):
        if department.parent_id is not None:
            continue
        if folder_repo.root_for_department(session, department.id) is not None:
            results.append(DemoSeedResult(slug=department.slug, created=False))
            continue
        folder_repo.create(
            session, name=department.name, parent_id=None, owner_department=department
        )
        log.info("root folder created", extra={"department": department.slug})
        results.append(DemoSeedResult(slug=department.slug, created=True))
    session.commit()
    return results
