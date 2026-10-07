"""Code-side ambiguity detection (BELIRSIZLIK_PLAN option 2 / Adım 2, Naci 07.10.2026):
before the LLM is called on the DOCUMENT_QUERY path, decide whether a scope-less question
("Lisans ne zaman alındı?", "Son tadil neyi değiştirdi?") lands on *several different*
documents or projects — then Balbal asks which one instead of enumerating (Tansu decision
(a)), without any model call (ADR-021 analog) and with every word a code constant
(ADR-014); the names in the question come from the retrieved chunks, i.e. from inside the
caller's `allowed_document_ids` set (G3).

Two signals, both required:

(i)  scope-less question — the terms that single documents out
     (`assist.specific_matched_terms`) are *all* document-class words (sözleşme, rapor,
     lisans, toplantı, …), the question names no project (`assist.project_words`), no
     candidate's document type or title (plan exclusion (b)) and asks for no list ("tüm",
     "hepsi", "listele").
(ii) spread — among the top `TOP_N` retrieved chunks at least two *groups* (group =
     project + document type; a version chain is one group) and the best chunk of the
     second group ranks at least `CLOSE` × the best chunk overall.

Thresholds (`TOP_N=15`, `CLOSE=0.5`) were tuned on ONE set — the five `ambiguous`
questions of `questions.json` v6 — in an LLM-free dry run (`scripts/dry_run_ambiguity.py`,
report `docs/reports/BELIRSIZLIK_REPORT.md` §1): 5/5 fire, one MIXED false positive that the
DOCUMENT_QUERY restriction removes. They are not to be re-tuned without a new held-out set.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.project import Project
from app.repositories.document_chunk_repo import RetrievedChunk
from app.services import assist
from app.services.search_query import question_terms, turkish_lower

TOP_N = 15
CLOSE = 0.5
MAX_TITLES = 3

# Words that name a *kind* of document rather than one document; a question whose only
# specific terms are of this kind has not said which document it means.
CLASS_WORDS: tuple[str, ...] = (
    "sözleşme",
    "rapor",
    "lisans",
    "toplantı",
    "tadil",
    "karar",
    "belge",
    "poliçe",
    "tutanak",
    "mektup",
    "dscr",
    "değer",
)
LIST_WORDS: frozenset[str] = frozenset({"tüm", "tümü", "hepsi", "listele", "hangileri", "her"})
LIST_PHRASES: tuple[str, ...] = ("hangi proje", "listele")

PROJECT_TEMPLATE = "Hangi projeyi kastediyorsunuz: {names}?"
DOCUMENT_TEMPLATE = "Hangi belgeyi kastediyorsunuz: {titles}?"

Axis = Literal["project", "document"]


@dataclass(frozen=True)
class Ambiguity:
    axis: Axis
    question: str
    documents: tuple[Document, ...]  # one representative per group, rank order
    groups: int


def _scope_less(session: Session, allowed: set[UUID], text: str) -> bool:
    terms = question_terms(text)
    lowered = {turkish_lower(t) for t in terms}
    if lowered & assist.project_words(session):
        return False
    low_text = turkish_lower(text)
    if lowered & LIST_WORDS or any(p in low_text for p in LIST_PHRASES):
        return False
    unmatched = assist.unmatched_terms(session, allowed, terms)
    specific = assist.specific_matched_terms(session, allowed, terms, unmatched)
    return all(
        any(turkish_lower(term).startswith(word) for word in CLASS_WORDS) for term in specific
    )


def _names_a_candidate(question: str, documents: tuple[Document, ...]) -> bool:
    """Plan exclusion (b), the document half: a question that spells out a candidate's
    document type or title ("Üretim lisansı ne zaman alındı?" when one group is of type
    "Üretim Lisansı") has given its scope — the class-word test alone would miss this,
    because "lisansı" is a class word (ANK-NEG-004 in the dry run, 07.10.2026)."""
    low = turkish_lower(question)
    for document in documents:
        for name in (document.document_type, document.title):
            if name and len(name) >= 4 and turkish_lower(name) in low:
                return True
    return False


def _groups(
    chunks: list[RetrievedChunk], documents: dict[UUID, Document]
) -> OrderedDict[tuple[str | None, str], tuple[float, Document]]:
    groups: OrderedDict[tuple[str | None, str], tuple[float, Document]] = OrderedDict()
    for chunk in chunks[:TOP_N]:
        document = documents.get(chunk.document_id)
        if document is None:
            continue
        key = (str(document.project_id) if document.project_id else None, document.document_type)
        if key not in groups:
            groups[key] = (chunk.rank, document)
    return groups


def _join(names: list[str]) -> str:
    return " mi, ".join(names[:-1]) + " mi, " + names[-1] + " mi" if len(names) > 1 else names[0]


def detect(
    session: Session,
    allowed: set[UUID],
    question: str,
    chunks: list[RetrievedChunk],
    documents: dict[UUID, Document],
) -> Ambiguity | None:
    """None unless both signals hold. `documents` are the retrieved documents (already
    inside `allowed`); nothing outside them is ever named."""
    if not chunks or not allowed:
        return None
    groups = _groups(chunks, documents)
    if len(groups) < 2:
        return None
    ranks = [rank for rank, _ in groups.values()]
    if ranks[0] <= 0 or ranks[1] < CLOSE * ranks[0]:
        return None
    representatives = tuple(doc for _, doc in groups.values())
    if _names_a_candidate(question, representatives):
        return None  # exclusion (b): the question names the document type / title it means
    if not _scope_less(session, allowed, question):
        return None

    project_ids = {d.project_id for d in representatives if d.project_id is not None}
    if len(project_ids) >= 2:
        names = [
            p.name
            for p in session.scalars(
                select(Project).where(Project.id.in_(list(project_ids))).order_by(Project.name)
            )
        ]
        return Ambiguity(
            "project", PROJECT_TEMPLATE.format(names=_join(names)), representatives, len(groups)
        )
    titles = [d.title for d in representatives[:MAX_TITLES]]
    return Ambiguity(
        "document", DOCUMENT_TEMPLATE.format(titles="; ".join(titles)), representatives, len(groups)
    )


def to_assist(ambiguity: Ambiguity, chunks: list[RetrievedChunk]) -> assist.Assist:
    """ADR-027 `Assist` with `kind=clarify`, the fixed template as the question and the
    representative documents (page of their best chunk) as "elimde şunlar var"."""
    best_page: dict[UUID, int] = {}
    for chunk in chunks:
        best_page.setdefault(chunk.document_id, chunk.page_number)
    available = tuple(
        assist.available_card(document, best_page.get(document.id))
        for document in ambiguity.documents[: assist.MAX_AVAILABLE]
    )
    return assist.Assist(
        kind="clarify", question=ambiguity.question, available=available, axis=ambiguity.axis
    )
