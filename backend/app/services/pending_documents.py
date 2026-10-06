"""Tansu Not 7 §3 — "the answer may be in a document that is still processing" (states
A/B/C/D), behind ASSIST_MODE. Runs *after* the answer, without the LLM: the model never
sees these documents (they have no chunks, or are not approved — ADR-021), so nothing here
can leak into the prompt; the user only learns that a document *exists* and what state it
is in, and only for documents the `/api/documents` list already shows them (G3).

    A  no answer + a matching queued/processing document → PROCESSING_NOTICE
    B  no answer + a matching unreadable document         → UNREADABLE_NOTICE (+ reason)
    C  answered  + a matching queued/processing document → CHANGE_NOTICE + title(s)
    D  no match                                            → nothing (today's behaviour)

Matching is metadata-only (title / type / counterparty / tags / extra fields — B-14's
`search_metadata`, the same lookup ADR-027's "elimde şunlar var" uses) on the question's
key terms, with the same exclusions as ADR-027: generic words and project names never
match on their own ("Ankara" would list every Ankara upload). Every sentence is a code
constant; the only variable text is a document title, and that comes from the gate.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.models.document import Document, IngestionStatus
from app.models.user import User
from app.repositories import document_repo
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.ask import PendingDocumentCard
from app.schemas.authorization import AuthorizationScope
from app.services.assist import GENERIC_TERMS, MIN_SPECIFIC_TERM_CHARS, project_words
from app.services.authorization import allowed_document_ids
from app.services.ingestion_errors import reason_for
from app.services.search_query import question_terms, turkish_lower

MAX_PENDING = 3
WINDOW_DAYS = 7
PendingState = Literal["A", "B", "C", "D"]
PendingStatus = Literal["uploaded", "ocr", "failed"]

PROCESSING_NOTICE = (
    "Bu sorunun cevabı henüz işlenmekte olan bir belgede olabilir. "
    "Belge hazır olduğunda tekrar sorarsanız cevaplayabilirim."
)
UNREADABLE_NOTICE = (
    "Bu soruyla ilgili olabilecek bir belge sistemde var ama okunamadığı için "
    "içeriğini kullanamıyorum."
)
CHANGE_NOTICE_PREFIX = (
    "Bu konuyla ilgili şu belge henüz işleniyor; işlendiğinde cevap değişebilir: "
)
# Ç-7 status note carried in the warning's `message` (Tansu §3 madde 4): the ready
# documents were searched and hold nothing — not "veri yok".
PROCESSED_NOTE = "Hazır (işlenmiş) belgelerde bu soruya ait bilgi bulunmuyor."

PROCESSING_STATUSES: frozenset[IngestionStatus] = frozenset(
    {IngestionStatus.uploaded, IngestionStatus.ocr}
)


@dataclass(frozen=True)
class PendingDocument:
    document_id: uuid.UUID
    title: str
    status: PendingStatus
    uploaded_at: datetime
    department: str | None
    reason: str | None  # failed only: the mapped Turkish line, never the code


@dataclass(frozen=True)
class PendingOutcome:
    state: PendingState = "D"
    notice: str | None = None
    documents: tuple[PendingDocument, ...] = ()


NO_PENDING = PendingOutcome()


def match_terms(session: Session, question: str) -> list[str]:
    """Question terms that may single a pending document out: ≥ 4 characters, not a generic
    word, not a project name (ADR-027's lists, so the two features agree)."""
    skip = GENERIC_TERMS | project_words(session)
    return [
        t
        for t in question_terms(question)
        if len(t) >= MIN_SPECIFIC_TERM_CHARS and turkish_lower(t) not in skip
    ]


def _card(document: Document) -> PendingDocument:
    failed = document.ingestion_status == IngestionStatus.failed
    status: PendingStatus = (
        "failed"
        if failed
        else ("ocr" if document.ingestion_status == IngestionStatus.ocr else "uploaded")
    )
    return PendingDocument(
        document_id=document.id,
        title=document.title,
        status=status,
        uploaded_at=document.created_at,
        department=document.department,
        reason=reason_for(document.ingestion_error) if failed else None,
    )


def find_matches(
    session: Session,
    user: User,
    department: str | None,
    question: str,
    *,
    exclude: Iterable[uuid.UUID] = (),
) -> list[PendingDocument]:
    """Unresolved documents (queued/processing, or failed however old) of the last 7 days
    inside the caller's *handling* set — `allowed_document_ids` with `include_pending`,
    exactly what `/api/documents` and `/api/documents/recent` show — whose metadata matches
    a key term of the question. Newest first, at most MAX_PENDING. `exclude` = the documents
    retrieval already read for this answer — whatever their status row says, they were not
    "unavailable" to Balbal."""
    allowed = allowed_document_ids(
        user,
        AuthorizationScope(department=department, include_pending=True),
        SqlDocumentIdsProvider(session),
    )
    if not allowed:
        return []
    since = datetime.now(UTC) - timedelta(days=WINDOW_DAYS)
    skip_ids = set(exclude)
    candidates = {
        d.id: d
        for d in document_repo.list_unresolved(session, allowed, since=since)
        if d.id not in skip_ids
    }
    if not candidates:
        return []
    terms = match_terms(session, question)
    if not terms:
        return []
    matched: dict[uuid.UUID, Document] = {}
    for term in terms:
        for document in document_repo.search_metadata(
            session, candidates, term, limit=len(candidates)
        ):
            matched.setdefault(document.id, document)
    ordered = sorted(matched.values(), key=lambda d: (d.created_at, d.id), reverse=True)
    return [_card(d) for d in ordered[:MAX_PENDING]]


def resolve(answered: bool, matches: Iterable[PendingDocument]) -> PendingOutcome:
    documents = tuple(matches)
    if not documents:
        return NO_PENDING
    processing = [d for d in documents if d.status != "failed"]
    if answered:
        if not processing:
            return NO_PENDING  # an unreadable document changes nothing about a given answer
        titles = "; ".join(d.title for d in processing)
        return PendingOutcome("C", CHANGE_NOTICE_PREFIX + titles, tuple(processing))
    if processing:
        return PendingOutcome("A", PROCESSING_NOTICE, documents)
    return PendingOutcome("B", UNREADABLE_NOTICE, documents)


def evaluate(
    session: Session,
    user: User,
    department: str | None,
    question: str,
    *,
    answered: bool,
    retrieved: Iterable[uuid.UUID] = (),
) -> PendingOutcome:
    return resolve(answered, find_matches(session, user, department, question, exclude=retrieved))


def pending_cards(outcome: PendingOutcome) -> list[PendingDocumentCard]:
    return [
        PendingDocumentCard(
            document_id=d.document_id,
            title=d.title,
            status=d.status,
            uploaded_at=d.uploaded_at,
            department=d.department,
            reason=d.reason,
        )
        for d in outcome.documents
    ]


def audit_json(
    assist: dict[str, Any] | None, outcome: PendingOutcome | None
) -> dict[str, Any] | None:
    """`audit_log.assist` (Naci SORU 8: no new column): the ADR-027 block plus what Not 7
    showed — state, sentence, documents — exactly as the user saw them (rule 4). None when
    neither feature produced anything, so flag-off rows stay NULL."""
    if outcome is None or outcome.state == "D":
        return assist
    payload: dict[str, Any] = dict(assist or {})
    payload["pending_state"] = outcome.state
    payload["pending_notice"] = outcome.notice
    payload["pending_documents"] = [c.model_dump(mode="json") for c in pending_cards(outcome)]
    return payload
