"""Demo project rows for tests that ask project-named questions (ADR-031: a project name the
`projects` table does not know is refused before retrieval — so a test that asks about
"Kızılova RES" must have that project on the table, as the seed does on a real deployment)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.project import Project
from app.repositories import project_repo

DEMO_PROJECTS: tuple[tuple[str, str], ...] = (
    ("Karatepe RES", "ANK_RES"),
    ("Kızılova RES", "IZM_RES"),
)


def ensure_projects(
    session: Session, projects: tuple[tuple[str, str], ...] = DEMO_PROJECTS
) -> dict[str, Project]:
    out: dict[str, Project] = {}
    for name, code in projects:
        existing = project_repo.get_by_code(session, code)
        if existing is None:
            existing = Project(name=name, code=code)
            session.add(existing)
            session.commit()
        out[code] = existing
    return out
