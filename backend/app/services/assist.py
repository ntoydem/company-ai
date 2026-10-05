"""Assist block (ADR-027, Tansu Not 2): "veri yok" is a no-fabrication rule, not a no-help
rule. When a question cannot be answered, the fixed no-answer sentence stays the verdict
(ADR-014) and this module adds, **in code**, what can honestly be said about the user's
own corpus: which question terms matched nothing, which document-side terms exist for them
(glossary, verified against the user's allowed documents), which allowed documents are
available, and at most one short clarifying question.

Two paths, one rule each:
- zero retrieved chunks → no LLM at all (ADR-021); the clarifying question is a fixed
  template;
- chunks retrieved but the model declined → the model may append one `SORU:` line; code
  parses it and keeps it only if it carries no digits/dates/currency and names no document
  the user may not see. Anything else is dropped silently — the worst case is today's
  behaviour, never a chattier fabrication.

Every lookup runs inside `allowed` (ADR-004): `search_fts(allowed_ids=…)`,
`search_metadata(session, allowed, …)`. Nothing here can surface a document the gate hides.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.document import Document
from app.repositories import document_repo
from app.repositories.document_chunk_repo import RetrievedChunk, search_fts
from app.schemas.ask import AssistAvailableDocument, AssistBlock
from app.services.search_glossary import expand_terms
from app.services.search_query import question_terms, turkish_lower

log = logging.getLogger(__name__)

AssistKind = Literal["none", "clarify", "term_mismatch"]

MAX_AVAILABLE = 5
MAX_CANDIDATE_TERMS = 5
MAX_QUESTION_CHARS = 200
# Shorter tokens ("RES", "kaç") are too common to say anything about a mismatch.
MIN_PROBE_TERM_CHARS = 3
# A metadata/"elimde şunlar var" hit must come from a term that actually narrows things:
# ≥ 4 characters ("RES" matches every project tag) and not matching more documents than
# we would list (a term found in > MAX_AVAILABLE documents is a non-term for this purpose).
MIN_SPECIFIC_TERM_CHARS = 4

QUESTION_MARKER = "SORU:"
CLARIFY_TEMPLATE = "Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?"


def term_mismatch_template(unmatched: Iterable[str]) -> str:
    quoted = ", ".join(f"«{t}»" for t in unmatched)
    return (
        f"Şu ifadeyi belgelerde bu haliyle bulamadım: {quoted}. Ne demek istediğinizi açar mısınız?"
    )


# A clarifying question carries no facts: digits (hence dates, amounts, years), currency
# and percent signs are all refused. Matches the eval runner's G1 rule for this field.
_FACT_TOKEN = re.compile(r"[0-9€$₺%]")
_SENTENCE_END = re.compile(r"[.!?]")


@dataclass(frozen=True)
class AvailableDocument:
    document_id: UUID
    title: str
    document_type: str
    document_date: date
    project_code: str | None
    page_number: int | None


@dataclass(frozen=True)
class Assist:
    kind: AssistKind = "none"
    question: str | None = None
    unmatched_terms: tuple[str, ...] = ()
    candidate_terms: tuple[str, ...] = ()
    available: tuple[AvailableDocument, ...] = ()
    # Why a model-written question was dropped (logged, never shown) — None when kept.
    dropped_reason: str | None = field(default=None, compare=False)


# ---------------------------------------------------------------- code-side lookups


def _available_card(document: Document, page_number: int | None) -> AvailableDocument:
    return AvailableDocument(
        document_id=document.id,
        title=document.title,
        document_type=document.document_type,
        document_date=document.document_date,
        project_code=document.project.code if document.project else None,
        page_number=page_number,
    )


def unmatched_terms(session: Session, allowed: set[UUID], terms: list[str]) -> list[str]:
    """Question terms that match no chunk the user may see — one LIMIT-1 FTS probe each."""
    if not allowed:
        return []
    out: list[str] = []
    for term in terms:
        if len(term) < MIN_PROBE_TERM_CHARS:
            continue
        if not search_fts(session, allowed_ids=allowed, query=term, top_k=1):
            out.append(term)
    return out


def candidate_terms(session: Session, allowed: set[UUID], unmatched: list[str]) -> list[str]:
    """Glossary document-side terms for the unmatched question terms, kept only when they
    really occur in an allowed document (a term the user cannot see is never suggested)."""
    if not allowed or not unmatched:
        return []
    out: list[str] = []
    for candidate in expand_terms([turkish_lower(t) for t in unmatched]):
        if len(out) >= MAX_CANDIDATE_TERMS:
            break
        if candidate in out:
            continue
        if search_fts(session, allowed_ids=allowed, query=candidate, top_k=1):
            out.append(candidate)
    return out


def available_from_metadata(
    session: Session, allowed: set[UUID], terms: list[str]
) -> list[AvailableDocument]:
    """Allowed documents whose title/type/counterparty/tags/extra fields contain a question
    term (B-14's `search_metadata`, same gate). Deduplicated, title order, ≤ MAX_AVAILABLE."""
    if not allowed:
        return []
    by_id: dict[UUID, Document] = {}
    for term in terms:
        if len(term) < MIN_SPECIFIC_TERM_CHARS:
            continue
        hits = document_repo.search_metadata(session, allowed, term, limit=MAX_AVAILABLE + 1)
        if len(hits) > MAX_AVAILABLE:
            continue  # too common to point anywhere (e.g. a project code carried by every tag)
        for document in hits:
            by_id.setdefault(document.id, document)
    ordered = sorted(by_id.values(), key=lambda d: (d.title, d.id))[:MAX_AVAILABLE]
    return [_available_card(document, None) for document in ordered]


def available_from_chunks(
    documents: dict[UUID, Document], chunks: list[RetrievedChunk]
) -> list[AvailableDocument]:
    """ "Elimde şunlar var": the retrieved (hence allowed) documents, best page each, by
    retrieval rank, ≤ MAX_AVAILABLE — Ç-7.1 step 3, built from `retrieved_document_ids`
    and never from the model's text."""
    best: dict[UUID, RetrievedChunk] = {}
    for chunk in chunks:
        current = best.get(chunk.document_id)
        if current is None or chunk.rank > current.rank:
            best[chunk.document_id] = chunk
    ranked = sorted(best.values(), key=lambda c: (-c.rank, c.document_id))
    out: list[AvailableDocument] = []
    for chunk in ranked[:MAX_AVAILABLE]:
        document = documents.get(chunk.document_id)
        if document is not None:
            out.append(_available_card(document, chunk.page_number))
    return out


# ---------------------------------------------------------------- the model's one line


def split_question_line(text: str) -> tuple[str, str | None]:
    """Separate the model's optional `SORU: …` line from its answer. Returns the answer
    without that line and the raw question (or None)."""
    kept: list[str] = []
    question: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if question is None and stripped.upper().startswith(QUESTION_MARKER):
            question = stripped[len(QUESTION_MARKER) :].strip()
            continue
        kept.append(line)
    return "\n".join(kept).strip(), question


def validate_question(
    question: str, *, hidden_titles: Iterable[str]
) -> tuple[str | None, str | None]:
    """Keep the model's clarifying question only if it is one short sentence ending in `?`,
    carries no digit/date/currency/percent, and names no document outside the user's
    allowed set. Returns (question or None, drop reason or None)."""
    text = " ".join(question.split())
    if not text:
        return None, "empty"
    if len(text) > MAX_QUESTION_CHARS:
        return None, "too long"
    if not text.endswith("?"):
        return None, "not a question"
    if _SENTENCE_END.search(text[:-1]):
        return None, "more than one sentence"
    if _FACT_TOKEN.search(text):
        return None, "contains a number, date, currency or percent"
    lowered = turkish_lower(text)
    for title in hidden_titles:
        if len(title) >= 6 and turkish_lower(title) in lowered:
            return None, "names a document outside the allowed set"
    return text, None


# ---------------------------------------------------------------- assembly


def _kind_for(
    unmatched: list[str], candidates: list[str], available: list[AvailableDocument]
) -> AssistKind:
    if unmatched and (candidates or available):
        return "term_mismatch"
    return "clarify"


def build_zero_chunk_assist(session: Session, allowed: set[UUID], question: str) -> Assist:
    """Nothing retrieved: no LLM (ADR-021). Everything here is a lookup inside `allowed`."""
    terms = question_terms(question)
    unmatched = unmatched_terms(session, allowed, terms)
    candidates = candidate_terms(session, allowed, unmatched)
    available = available_from_metadata(session, allowed, terms)
    kind = _kind_for(unmatched, candidates, available)
    text = term_mismatch_template(unmatched) if kind == "term_mismatch" else CLARIFY_TEMPLATE
    return Assist(
        kind=kind,
        question=text,
        unmatched_terms=tuple(unmatched),
        candidate_terms=tuple(candidates),
        available=tuple(available),
    )


def build_insufficient_assist(
    session: Session,
    allowed: set[UUID],
    question: str,
    *,
    documents: dict[UUID, Document],
    chunks: list[RetrievedChunk],
    model_question: str | None,
) -> Assist:
    """Chunks reached the prompt, the model still declined: list what was retrieved (code),
    detect unmatched terms (code), keep the model's one question only if it passes
    `validate_question`; otherwise fall back to the fixed template."""
    terms = question_terms(question)
    unmatched = unmatched_terms(session, allowed, terms)
    candidates = candidate_terms(session, allowed, unmatched)
    # "Elimde şunlar var" only when something specific in the question did match — if the
    # retrieved pages came from short, generic tokens alone ("RES", "kaç"), listing them
    # would suggest the corpus knows the subject when it does not.
    specific_matched = [
        t for t in terms if len(t) >= MIN_SPECIFIC_TERM_CHARS and t not in unmatched
    ]
    available = available_from_chunks(documents, chunks) if specific_matched else []
    kind = _kind_for(unmatched, candidates, available)
    kept: str | None = None
    reason: str | None = None
    if model_question is not None:
        kept, reason = validate_question(
            model_question, hidden_titles=document_repo.titles_outside(session, allowed)
        )
        if reason is not None:
            log.info("assist question dropped", extra={"reason": reason})
    text = kept or (
        term_mismatch_template(unmatched) if kind == "term_mismatch" else CLARIFY_TEMPLATE
    )
    return Assist(
        kind=kind,
        question=text,
        unmatched_terms=tuple(unmatched),
        candidate_terms=tuple(candidates),
        available=tuple(available),
        dropped_reason=reason,
    )


# ---------------------------------------------------------------- wire / audit shapes


def assist_block(assist: Assist | None) -> AssistBlock | None:
    """`AskResponse.assist`: None stays None (ASSIST_MODE off, or an answered reply)."""
    if assist is None:
        return None
    return AssistBlock(
        kind=assist.kind,
        question=assist.question,
        unmatched_terms=list(assist.unmatched_terms),
        candidate_terms=list(assist.candidate_terms),
        available=[
            AssistAvailableDocument(
                document_id=a.document_id,
                title=a.title,
                document_type=a.document_type,
                document_date=a.document_date,
                project_code=a.project_code,
                page_number=a.page_number,
            )
            for a in assist.available
        ],
    )


def assist_json(assist: Assist | None) -> dict[str, Any] | None:
    """`audit_log.assist`: exactly what the user saw (rule 4), plus why a model question was
    dropped when it was — the eval and a later review read both."""
    block = assist_block(assist)
    if block is None or assist is None:
        return None
    payload: dict[str, Any] = block.model_dump(mode="json")
    if assist.dropped_reason is not None:
        payload["dropped_reason"] = assist.dropped_reason
    return payload
