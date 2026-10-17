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
  naming only the projects the user can see), so the dominant-project guess never fires;
- the question names no project and asks for a value (İş Emri 2026-10-16N1) → the caller
  asks which project, one sentence, without the LLM (`unnamed_value_clarification`).

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
from app.repositories.document_chunk_repo import RetrievedChunk, document_ids_matching
from app.repositories.document_repo import search_metadata
from app.services.assist import is_existence_question, named_project_codes
from app.services.search_glossary import CONCEPT_GLOSSARY, GLOSSARY, expand_terms, metadata_terms
from app.services.search_query import (
    QUESTION_STOPWORDS,
    question_terms,
    turkish_fold,
    turkish_lower,
)

# "<Özel Ad> RES/GES" — the project-naming pattern of this company's library. The name word
# before the suffix may be any case (ADR-033, İş Emri 2026-10-16T3: "bursa RES"/"Bursa Res"
# must be seen as a project mention too, not silently pass through unrecognised) — case only
# ever decided whether the *rest* of the pipeline treated it as a proper noun, and
# `_NOT_A_NAME`/`known` already filter case-insensitively below. The RES/GES suffix itself
# is matched case-insensitively too (scoped `(?i:...)`, so the captured text still carries
# the question's own casing for the mention string).
_PROJECT_MENTION = re.compile(r"(?<![\w'’])(\w[\wçğıöşüâîû]*)\s+(?i:(RES|GES))(?![\w])")
# Determiners and question words that may precede "RES" at the start of a sentence
# ("Hangi RES …", "Bu RES …") — never a project name.
_NOT_A_NAME = frozenset(
    turkish_fold(w)
    for w in QUESTION_STOPWORDS
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
    project's old name counts as unknown too (the table is the single source). Comparison
    is case/ASCII-fold-insensitive (ADR-033): "Kizilova RES" folds to the same word as
    "Kızılova RES" and is recognised as known, not refused."""
    known: set[str] = set()
    for project in session.scalars(select(Project).where(Project.is_active.is_(True))).all():
        for raw in (project.name, project.code):
            known.update(w for w in re.split(r"[^\w]+", turkish_fold(raw)) if w)
    out: list[str] = []
    for match in _PROJECT_MENTION.finditer(question):
        word, suffix = match.group(1), match.group(2)
        folded = turkish_fold(word)
        if folded in _NOT_A_NAME or folded in known:
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


# İş Emri 2026-10-16N1 (Tansu 16.10, madde 7): a question that names no project and asks for
# a value (a figure, a date, a condition) is answered by code with one question — which
# project — and no model call. Discovery questions (`is_existence_question`) keep the F-3
# grouped list; a question about the projects themselves or across them ("hangi projenin",
# "her proje için ayrı ayrı", "tüm projeler") or about the company keeps today's path (the
# per-project full answer is Ürün 2, not built here).
UNNAMED_PROJECT_QUESTION = "Hangi proje için sormak istiyorsunuz?"
_ACROSS_PROJECTS = re.compile(
    r"\b(?:hangi\s+(?:(?:res|ges|santral)\w*\s+)?proje\w*|hangi\s+(?:res|ges|santral)\w*"
    r"|(?:her|tüm|bütün|iki|diğer|başka)\s+(?:bir\s+)?(?:(?:res|ges)\s+)?proje\w*"
    r"|proje\s+proje|projeler\w*|ayrı\s+ayrı|şirket\w*|holding\w*)\b"
)
# A question at all: a question mark, an interrogative or the yes/no particle. Chit-chat
# without one ("merhaba", "teşekkürler") is not a value question.
_VALUE_SIGNAL = re.compile(
    r"\?|\b(?:kaç\w*|ne|neyi|neye|nedir|neydi|neden|niçin|niye|nasıl|kim\w*|hangi\w*"
    r"|m[ıiuü](?:dır|dir|dur|dür|ydı|ydi|ydu|ydü)?)\b"
)


def asks_across_projects(question: str) -> bool:
    """The project is the subject ("Hangi projenin üretim lisansı var?") or the user asked for
    every project / the company — not a question missing its project."""
    return bool(_ACROSS_PROJECTS.search(turkish_lower(question)))


def is_unnamed_value_question(
    session: Session, question: str, previous_question: str | None = None
) -> bool:
    """No project named — in the question or in the previous question it follows (Ç-2
    context), known or unknown — and a value is asked: not a discovery question, not a
    question across projects. Text and the `projects` table only; the caller still applies
    `unnamed_value_clarification` after retrieval."""
    if not _VALUE_SIGNAL.search(turkish_lower(question)):
        return False
    if is_existence_question(question) or asks_across_projects(question):
        return False
    return not any(
        text and (named_project_codes(session, text) or unknown_project_names(session, text))
        for text in (question, previous_question)
    )


def unnamed_project_question(visible: list[str]) -> str:
    """The one sentence, with the user's own projects in brackets (G1: names, no digits)."""
    if not visible:
        return UNNAMED_PROJECT_QUESTION
    return f"{UNNAMED_PROJECT_QUESTION[:-1]} ({', '.join(visible)})?"


def unnamed_value_clarification(
    session: Session, allowed: set[UUID], chunks: list[RetrievedChunk], *, question: str
) -> str | None:
    """The project question for an unnamed value question — or None when there is no project
    to ask about: the user sees no project document, the best-ranked retrieved chunk is a
    group document (a company question: "Denetim komitesi üyeleri hangi kararla atandı?"), or
    the topic is in no project document of the user (ADR-035, S-2). The options are the
    projects holding the topic (`projects_with_data`); a single one is still asked (S-3), an
    undetermined topic keeps every visible project (S-1). Only `allowed` and the
    already-gated chunks are read (T-5)."""
    visible = visible_project_names(session, allowed)
    if not visible:
        return None
    if chunks:
        top = max(chunks, key=lambda chunk: chunk.rank)
        scope = session.scalar(select(Document.project_scope).where(Document.id == top.document_id))
        if scope == ProjectScope.group:
            return None
    with_data = projects_with_data(session, allowed, question)
    if with_data is None:
        return unnamed_project_question(visible)
    if not with_data:
        return None
    return unnamed_project_question(with_data)


# İş Emri 2026-10-17P1K (ADR-035, Tansu 16.10 madde 1): the options of the project question
# are the projects with at least one document — inside `allowed` — whose text (FTS, the
# retrieval predicate) or catalogue fields (`search_metadata`) carry the question's topic.
# Decided per document: no top-k, no rank. A term found in more than GENERIC_SHARE of the
# user's own project documents does not tell projects apart and is ignored; the share is
# taken from `allowed` only, so hidden documents cannot shape it (T-5).
GENERIC_SHARE = 0.5


def _concept_terms(lowered: list[str]) -> set[str]:
    """The lowered terms a glossary concept covers (a GLOSSARY / CONCEPT_GLOSSARY key; one-word
    keys prefix-match, a multi-word key covers its words when the whole key is present) —
    the topic anchor: "son", "güncel", "kadar" never outweigh "tadil", "sigorta", "DSCR"."""
    joined = " ".join(lowered)
    covered: set[str] = set()
    for key in (*GLOSSARY, *CONCEPT_GLOSSARY):
        words = key.split()
        if len(words) > 1 and key not in joined:
            continue
        covered.update(term for term in lowered if any(term.startswith(w) for w in words))
    return covered


def _term_evidence(session: Session, allowed: set[UUID], term: str) -> set[UUID]:
    """Documents in `allowed` whose chunks match the term, the glossary stem it starts with
    ("vadesi" → "vade": the `turkish` stemmer does not join the two) or the stem's document
    terms — or whose catalogue fields contain the term or its title-side concept terms."""
    lowered = turkish_lower(term)
    stems = [key for key in (*GLOSSARY, *CONCEPT_GLOSSARY) if lowered.startswith(key)]
    query = " OR ".join(dict.fromkeys([term, *stems, *expand_terms([lowered])]))
    hits = document_ids_matching(session, allowed_ids=allowed, query=query)
    for needle in (term, *metadata_terms([lowered])):
        hits.update(d.id for d in search_metadata(session, allowed, needle, limit=len(allowed)))
    return hits


def projects_with_data(session: Session, allowed: set[UUID], question: str) -> list[str] | None:
    """Names (ordered like `visible_project_names`) of the active projects holding the topic.
    `[]`: there was a topic but no project document of the user carries it. None: the topic
    could not be determined (no term left once the zero-evidence and generic ones are out).

    Topic = the non-generic terms a glossary concept covers; without any, the non-generic
    terms found in some allowed document. Projects are the UNION over topic terms — an
    intersection would drop a project whose contract happens not to use one of the words."""
    if not allowed:
        return None
    rows = session.execute(
        select(Document.id, Project.name)
        .join(Project, Document.project_id == Project.id)
        .where(
            Document.id.in_(list(allowed)),
            Document.project_scope == ProjectScope.project,
            Project.is_active.is_(True),
        )
        .order_by(Project.name, Document.id)
    ).all()
    project_of = {document_id: name for document_id, name in rows}
    if not project_of:
        return None
    terms = question_terms(question)
    concepts = _concept_terms([turkish_lower(term) for term in terms])
    anchors: list[set[UUID]] = []
    others: list[set[UUID]] = []
    for term in terms:
        evidence = _term_evidence(session, allowed, term)
        in_projects = evidence & project_of.keys()
        if len(in_projects) > GENERIC_SHARE * len(project_of):
            continue
        if turkish_lower(term) in concepts:
            anchors.append(in_projects)
        elif evidence:
            others.append(in_projects)
    topic = anchors or others
    if not topic:
        return None
    selected = {project_of[document_id] for hits in topic for document_id in hits}
    return [name for name in dict.fromkeys(project_of.values()) if name in selected]
