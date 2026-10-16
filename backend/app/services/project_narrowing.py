"""Şart 1 — project narrowing of the `/api/ask` candidate package (İş Emri 2026-10-15A2,
ADR-031). Runs **after** `allowed_document_ids` (ADR-004) and only ever removes candidates:

- the question names one or more projects (`assist.named_project_codes`) → every retrieved
  chunk, listed document and audit `chunks_retrieved` entry belongs to one of those projects
  or is a group document (`project_scope = group`); another project's document is not a
  candidate at all — the LLM never sees it, the F-3 list never shows it;
- the question names no project → nothing changes here; the Adım 4 project axis
  (`dominant` / `disambiguate` / `none`) decides as before;
- the question names a project that the `projects` table does not know ("Bursa RES") →
  the caller answers without the LLM (`term_mismatch` + the fixed verdict + one question
  naming only the projects the user can see), so the dominant-project guess never fires.

Flag-independent by design (Şart 1 is a standing principle, not an Ek-F presentation): the
same narrowing applies with `EK_F_MODE` on or off.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.document import Document, ProjectScope
from app.models.project import Project
from app.repositories.document_chunk_repo import RetrievedChunk
from app.services.search_query import QUESTION_STOPWORDS, turkish_lower

# "<Özel Ad> RES/GES" — the project-naming pattern of this company's library. The word
# before the suffix must be a proper noun: capitalised, not a question word/determiner.
_PROJECT_MENTION = re.compile(r"(?<![\w'’])([A-ZÇĞİÖŞÜ][\wçğıöşüâîû]*)\s+(RES|GES)(?![\w])")
# Determiners and question words that may precede "RES" at the start of a sentence
# ("Hangi RES …", "Bu RES …") — never a project name.
_NOT_A_NAME = frozenset(
    QUESTION_STOPWORDS
    | {
        "her",
        "iki",
        "üç",
        "tüm",
        "bütün",
        "diğer",
        "başka",
        "hiçbir",
        "yeni",
        "eski",
        "ilk",
        "son",
        "hangi",
        "bu",
        "şu",
        "o",
        "bir",
        "kaç",
        "proje",
        "projeler",
    }
)


@dataclass(frozen=True)
class ProjectNarrowing:
    """Outcome for one question: the codes the question names (possibly none), and the
    candidate document ids after narrowing (`scoped`) — equal to `allowed` when no project
    is named. `dropped` counts the allowed documents that fell out (for logs/measurement)."""

    named_codes: frozenset[str]
    scoped: frozenset[UUID]
    dropped: int = 0

    @property
    def active(self) -> bool:
        return bool(self.named_codes)


def narrow_allowed(
    session: Session, allowed: set[UUID], named_codes: Iterable[str]
) -> ProjectNarrowing:
    """`allowed ∩ (project ∈ named ∪ group)`. With no named code the allowed set is returned
    unchanged — the project axis (Adım 4) is then the only project logic in play."""
    codes = frozenset(named_codes)
    if not codes or not allowed:
        return ProjectNarrowing(named_codes=codes, scoped=frozenset(allowed))
    project_ids = list(
        session.scalars(select(Project.id).where(Project.code.in_(sorted(codes)))).all()
    )
    rows = session.scalars(
        select(Document.id).where(
            Document.id.in_(list(allowed)),
            or_(
                Document.project_id.in_(project_ids),
                Document.project_scope == ProjectScope.group,
            ),
        )
    )
    scoped = frozenset(rows)
    return ProjectNarrowing(named_codes=codes, scoped=scoped, dropped=len(allowed) - len(scoped))


def narrow_chunks(chunks: list[RetrievedChunk], scoped: frozenset[UUID]) -> list[RetrievedChunk]:
    """The retrieved chunks that belong to a scoped document, rank order preserved."""
    return [chunk for chunk in chunks if chunk.document_id in scoped]


def unknown_project_names(session: Session, question: str) -> list[str]:
    """Project mentions ("Bursa RES") whose name word belongs to no row of the `projects`
    table — the words of every project name and code are the reference, so a renamed
    project's old name counts as unknown too (the table is the single source)."""
    known: set[str] = set()
    for project in session.scalars(select(Project).where(Project.is_active.is_(True))).all():
        for raw in (project.name, project.code):
            known.update(w for w in re.split(r"[^\w]+", turkish_lower(raw)) if w)
    out: list[str] = []
    for match in _PROJECT_MENTION.finditer(question):
        word, suffix = match.group(1), match.group(2)
        lowered = turkish_lower(word)
        if lowered in _NOT_A_NAME or lowered in known:
            continue
        mention = f"{word} {suffix}"
        if mention not in out:
            out.append(mention)
    return out


def visible_project_names(session: Session, allowed: set[UUID]) -> list[str]:
    """Names of the projects the user actually has documents for (inside `allowed`, ADR-004)
    — the only projects an "unknown project" question may offer as alternatives (G3)."""
    if not allowed:
        return []
    stmt = (
        select(Project.name)
        .join(Document, Document.project_id == Project.id)
        .where(Document.id.in_(list(allowed)), Project.is_active.is_(True))
        .distinct()
        .order_by(Project.name)
    )
    return list(session.scalars(stmt).all())


def unknown_project_question(unknown: list[str], visible: list[str]) -> str:
    """One question, project names only (no digits, G1): "Bu adda bir proje kayıtlı değil;
    hangi projeyi kastediyorsunuz: X mi, Y mi?" — or, with nothing visible, the bare
    statement plus a generic question."""
    head = "Bu adda bir proje kayıtlı değil"
    if not visible:
        return f"{head}; hangi projeyi kastediyorsunuz?"
    if len(visible) == 1:
        return f"{head}; {visible[0]} projesini mi kastediyorsunuz?"
    if len(visible) == 2:
        return f"{head}; hangi projeyi kastediyorsunuz: {visible[0]} mi, {visible[1]} mi?"
    return (
        f"{head}; hangi projeyi kastediyorsunuz: "
        + ", ".join(visible[:-1])
        + f" yoksa {visible[-1]} mi?"
    )
