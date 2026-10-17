"""Project scope of the Excel path (İş Emri 2026-10-17P2A, ADR-036). Runs **after**
`allowed_document_ids` (ADR-004) and only ever removes candidates (T-5):

- the user's own question names a project → the catalogue is that project's workbooks plus
  group workbooks (`narrow_allowed`, ADR-031 Şart 1); another project's workbook is never
  loaded, so neither a function nor a SELECT can read it;
- the question names no project and the plan read a workbook whose type (`document_type`)
  more than one visible project holds → no figure, no answering model: one question, which
  project (`project_question`), naming only the projects that hold that data;
- one project holds it → answered as before, with the project's name on the answer
  (`answer_project`, Tansu 17.10 madde 9);
- two or more projects named → the same question ("Hangisi?", madde 10); a per-project Excel
  answer (Ü-3) is not built here.

The workbook → project link is `documents.project_id`, not a ranking (ADR-036)."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.project import Project
from app.repositories import document_repo
from app.services.assist import named_project_codes
from app.services.project_narrowing import narrow_allowed, unnamed_project_question


@dataclass(frozen=True)
class ExcelScope:
    """The codes the user's question names and the Excel documents left as candidates."""

    named_codes: frozenset[str]
    documents: list[Document]


def scope_workbooks(session: Session, allowed: set[UUID], question: str) -> ExcelScope:
    """`allowed ∩ (project ∈ named ∪ group)` → the ready Excel documents of that set; with
    no project named, every allowed workbook (as before)."""
    narrowing = narrow_allowed(session, allowed, named_project_codes(session, question))
    return ExcelScope(
        named_codes=narrowing.named_codes,
        documents=document_repo.list_excel_by_ids(session, narrowing.scoped),
    )


def _type_key(document: Document) -> str | None:
    return document.document_type.strip().casefold() if document.document_type else None


def _project_names(session: Session, project_ids: set[UUID]) -> list[str]:
    """Ordered like `visible_project_names` (DB collation)."""
    stmt = select(Project.name).where(Project.id.in_(list(project_ids))).order_by(Project.name)
    return list(session.scalars(stmt).all())


def project_question(
    session: Session,
    scope: ExcelScope,
    used_ids: Iterable[UUID],
    workbooks: Sequence[Document],
) -> str | None:
    """The project question for a computed result — None when the result may be shown.
    `used_ids`: the workbooks the result was read from; `workbooks`: the loaded catalogue.
    A result read only from group workbooks is company data and is never questioned."""
    used = set(used_ids)
    used_projects = [d for d in workbooks if d.id in used and d.project_id is not None]
    if not used_projects:
        return None
    if len(scope.named_codes) == 1:
        return None
    if scope.named_codes:
        # Madde 10: two projects named, one plan → which one; the catalogue already holds
        # only the named projects' (and group) workbooks.
        holders = {d.project_id for d in workbooks if d.project_id is not None}
    else:
        types = {_type_key(d) for d in used_projects}
        # An untyped workbook cannot be matched by type: every project with a workbook in
        # the catalogue counts (asks more, never answers for the wrong project).
        holders = {
            d.project_id
            for d in workbooks
            if d.project_id is not None and (None in types or _type_key(d) in types)
        }
        if len(holders) < 2:
            return None
    return unnamed_project_question(_project_names(session, {h for h in holders if h}))


def answer_project(
    session: Session, scope: ExcelScope, used_ids: Iterable[UUID], workbooks: Sequence[Document]
) -> str | None:
    """Madde 9: the project an unnamed question was answered for — the one project of the
    workbooks the result was read from; None when a project was named or none applies."""
    if scope.named_codes:
        return None
    used = set(used_ids)
    projects = {d.project_id for d in workbooks if d.id in used and d.project_id is not None}
    if len(projects) != 1:
        return None
    names = _project_names(session, {p for p in projects if p})
    return names[0] if names else None
