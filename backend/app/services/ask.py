"""`/api/ask` pipeline (SPEC_02 §9): authorize → retrieve → chain evaluation → prompt →
LLM → cited sources. Only chunks returned by `retrieve()` — hence only allowed ones
(ADR-004) — ever reach the prompt; nothing else is read."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.request_id import get_request_id
from app.models.user import User
from app.repositories import audit_log_repo, document_repo
from app.repositories.document_chunk_repo import RetrievedChunk
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.ask import AskRequest, SourceCard
from app.schemas.authorization import AuthorizationScope
from app.schemas.retrieval import RetrievalFilters
from app.services import answer_prompt
from app.services.authorization import allowed_document_ids
from app.services.llm import LLMClient, LLMError, LLMRequest
from app.services.retrieval import retrieve
from app.services.search_query import build_search_query
from app.services.version_chain import evaluate_version_chains

log = logging.getLogger(__name__)

# Always "DOCUMENT_QUERY": the router (ADR-010) lands in Phase 4.3; `/api/ask` only ever
# does document Q&A today.
_QUERY_TYPE = "DOCUMENT_QUERY"


@dataclass(frozen=True)
class AskResult:
    answer: str
    answered: bool
    sources: list[SourceCard] = field(default_factory=list)
    retrieved_document_ids: list[UUID] = field(default_factory=list)
    model: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0


def _no_answer() -> AskResult:
    return AskResult(answer=answer_prompt.NO_ANSWER_TEXT, answered=False)


def _source_cards(
    refs: list[str], sources: list[answer_prompt.PromptSource]
) -> tuple[list[SourceCard], list[str]]:
    by_ref = {source.ref: source for source in sources}
    cards: list[SourceCard] = []
    seen: set[tuple[UUID, int]] = set()
    unknown: list[str] = []
    for ref in refs:
        source = by_ref.get(ref)
        if source is None:
            unknown.append(ref)
            continue
        key = (source.document.id, source.chunk.page_number)
        if key in seen:
            continue
        seen.add(key)
        document = source.document
        cards.append(
            SourceCard(
                ref=ref,
                document_id=document.id,
                title=document.title,
                page_number=source.chunk.page_number,
                document_date=document.document_date,
                effective_date=document.effective_date,
                version=document.version,
                status=document.status,
                is_current=source.position.is_current,
                supersedes_title=source.position.supersedes_title,
                superseded_by_title=source.position.superseded_by_title,
            )
        )
    return cards, unknown


def _write_audit_log(
    session: Session,
    user: User,
    request: AskRequest,
    *,
    retrieved_ids: list[UUID],
    chunks: list[RetrievedChunk],
    answer: str,
    sources: list[SourceCard],
    model: str | None,
    tokens_in: int,
    tokens_out: int,
    execution_ms: int,
    error: str | None,
) -> None:
    """SPEC_06 §1: one row per `/api/ask` call, success or failure. Never raises — a
    logging failure must never break the answer the user already has (ADR-006 pattern);
    the caller's response is unaffected either way. `cost_estimate` stays `NULL` in V0 —
    no invented per-model pricing (Phase 3.2 SORU 2, docs/plans/PHASE_3_4_PLAN.md)."""
    try:
        audit_log_repo.create(
            session,
            user_id=user.id,
            question=request.question,
            query_type=_QUERY_TYPE,
            scope_department=request.department,
            scope_project=request.project_id,
            documents_retrieved=retrieved_ids,
            chunks_retrieved=[
                {"document_id": str(c.document_id), "page_number": c.page_number, "rank": c.rank}
                for c in chunks
            ],
            answer=answer,
            sources=[card.model_dump(mode="json") for card in sources],
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_estimate=None,
            execution_ms=execution_ms,
            request_id=get_request_id(),
            error=error,
        )
    except Exception:
        log.exception("audit log write failed")


def answer_question(
    session: Session, user: User, request: AskRequest, llm: LLMClient, settings: Settings
) -> AskResult:
    started = time.perf_counter()
    filters = RetrievalFilters(department=request.department, project_id=request.project_id)
    query = build_search_query(request.question)
    chunks = retrieve(session, user, query, filters, raw_question=request.question) if query else []
    retrieved_ids = list(dict.fromkeys(chunk.document_id for chunk in chunks))

    if not chunks:
        result = _no_answer()
    else:
        scope = AuthorizationScope(department=request.department, project_id=request.project_id)
        allowed = allowed_document_ids(user, scope, SqlDocumentIdsProvider(session))
        documents = document_repo.load_with_chains(session, retrieved_ids, allowed_ids=allowed)
        by_id = {document.id: document for document in documents}
        chain = evaluate_version_chains(documents, settings.demo_today)
        sources = answer_prompt.order_sources(chunks, by_id, chain)

        user_prompt = answer_prompt.build_user_prompt(
            request.question, sources, settings.demo_today
        )
        try:
            response = llm.complete(
                LLMRequest(
                    system=answer_prompt.SYSTEM_PROMPT,
                    user=user_prompt,
                    model=settings.llm_model_answer,
                    max_output_tokens=settings.llm_max_output_tokens,
                    reasoning_effort=settings.llm_reasoning_effort,
                )
            )
        except LLMError as exc:
            _write_audit_log(
                session,
                user,
                request,
                retrieved_ids=retrieved_ids,
                chunks=chunks,
                answer="",
                sources=[],
                model=None,
                tokens_in=0,
                tokens_out=0,
                execution_ms=round((time.perf_counter() - started) * 1000),
                error=str(exc),
            )
            raise
        if answer_prompt.is_no_answer(response.text):
            result = AskResult(
                answer=answer_prompt.NO_ANSWER_TEXT,
                answered=False,
                retrieved_document_ids=retrieved_ids,
                model=response.model,
                tokens_in=response.tokens_in,
                tokens_out=response.tokens_out,
            )
        else:
            refs = answer_prompt.parse_citations(response.text)
            cards, unknown = _source_cards(refs, sources)
            if unknown:
                log.warning("unknown citation labels", extra={"labels": unknown})
            if not cards:
                log.warning("answer without citations")
            result = AskResult(
                answer=response.text.strip(),
                answered=True,
                sources=cards,
                retrieved_document_ids=retrieved_ids,
                model=response.model,
                tokens_in=response.tokens_in,
                tokens_out=response.tokens_out,
            )

    log.info(
        "ask completed",
        extra={
            "user_id": str(user.id),
            "question": request.question[:200],
            "retrieved_document_ids": [str(i) for i in result.retrieved_document_ids],
            "cited_document_ids": [str(card.document_id) for card in result.sources],
            "answered": result.answered,
            "model": result.model,
            "tokens_in": result.tokens_in,
            "tokens_out": result.tokens_out,
            "duration_ms": round((time.perf_counter() - started) * 1000),
        },
    )
    _write_audit_log(
        session,
        user,
        request,
        retrieved_ids=result.retrieved_document_ids,
        chunks=chunks,
        answer=result.answer,
        sources=result.sources,
        model=result.model,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        execution_ms=round((time.perf_counter() - started) * 1000),
        error=None,
    )
    return result
