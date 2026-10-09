"""`/api/ask` pipeline (SPEC_02 §9): authorize → retrieve → chain evaluation → prompt →
LLM → cited sources. Only chunks returned by `retrieve()` — hence only allowed ones
(ADR-004) — ever reach the prompt; nothing else is read."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field, replace
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.user import User
from app.repositories import document_repo
from app.repositories.document_chunk_repo import RetrievedChunk
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.ask import AskRequest, SourceCard
from app.schemas.authorization import AuthorizationScope
from app.schemas.retrieval import RetrievalFilters
from app.services import answer_prompt
from app.services.assist import (
    Assist,
    ProjectAxisDecision,
    available_from_chunks,
    build_disambiguate_assist,
    build_insufficient_assist,
    build_zero_chunk_assist,
    classify_project_axis,
    downgrade_existence_disambiguate,
    named_project_codes,
    project_distribution,
    render_no_data,
    split_question_line,
)
from app.services.audit_writer import write_audit_row
from app.services.authorization import allowed_document_ids
from app.services.llm import LLMClient, LLMError, LLMRequest
from app.services.retrieval import retrieve
from app.services.search_query import build_search_query
from app.services.temporal import today as temporal_today
from app.services.tr_format import polish_answer
from app.services.version_chain import evaluate_version_chains

log = logging.getLogger(__name__)

QUERY_TYPE = "DOCUMENT_QUERY"


@dataclass(frozen=True)
class AskResult:
    answer: str
    answered: bool
    sources: list[SourceCard] = field(default_factory=list)
    retrieved_document_ids: list[UUID] = field(default_factory=list)
    model: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    # What retrieval returned (for the audit row's `chunks_retrieved`); kept on the result
    # so a caller that owns the audit row (the router, Phase 4.3) can write it.
    chunks: list[RetrievedChunk] = field(default_factory=list)
    # ADR-027: code-generated help next to a no-answer; None when ASSIST_MODE is off.
    assist: Assist | None = None


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
                supersedes_document_id=source.position.supersedes_document_id,
                superseded_by_document_id=source.position.superseded_by_document_id,
                is_initial=source.position.is_initial,
                project_code=document.project.code if document.project else None,
                project_name=document.project.name if document.project else None,
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
    assist: Assist | None = None,
    previous_question: str | None = None,
) -> None:
    """SPEC_06 §1: one row per `/api/ask` call, success or failure."""
    write_audit_row(
        session,
        user,
        question=request.question,
        query_type=QUERY_TYPE,
        scope_department=request.department,
        scope_project=None,
        documents_retrieved=retrieved_ids,
        chunks=chunks,
        answer=answer,
        sources=sources,
        excel_sources=[],
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        execution_ms=execution_ms,
        error=error,
        assist=assist,
        previous_question=previous_question,
    )


def answer_question(
    session: Session,
    user: User,
    request: AskRequest,
    llm: LLMClient,
    settings: Settings,
    *,
    write_audit: bool = True,
) -> AskResult:
    """`write_audit=False` (Phase 4.3): the caller — the router — owns the one audit row of
    the call and writes it from the returned `AskResult` (SORU 2: one row per call)."""
    started = time.perf_counter()
    filters = RetrievalFilters(department=request.department)
    query = build_search_query(request.question)
    chunks = retrieve(session, user, query, filters, raw_question=request.question) if query else []
    retrieved_ids = list(dict.fromkeys(chunk.document_id for chunk in chunks))

    if not chunks:
        result = _no_answer()
        if settings.assist_computations:
            # ADR-027/ADR-021: still no LLM here — every lookup stays inside `allowed`.
            scope = AuthorizationScope(department=request.department)
            allowed = allowed_document_ids(user, scope, SqlDocumentIdsProvider(session))
            zero_assist = build_zero_chunk_assist(
                session,
                allowed,
                request.question,
                ek_f=settings.ek_f_enabled,
                disambig_spread=settings.project_axis_disambig_spread,
                dominant_share=settings.project_axis_dominant_share,
            )
            result = replace(result, assist=zero_assist)
            if settings.ek_f_enabled:
                # ADR-030 F-5: the pattern replaces the fixed sentence for the user.
                result = replace(result, answer=render_no_data(zero_assist, request.question))
    else:
        scope = AuthorizationScope(department=request.department)
        allowed = allowed_document_ids(user, scope, SqlDocumentIdsProvider(session))
        documents = document_repo.load_with_chains(session, retrieved_ids, allowed_ids=allowed)
        by_id = {document.id: document for document in documents}
        # Adım 4 (ADR-030, 09.10.2026): the project axis is classified from these same
        # retrieved documents *before* the prompt is built — a genuinely ambiguous question
        # (no project named, candidates split close to evenly between ≥ 2 projects) must
        # never reach the LLM at all (Ü-3/F-4), the same ADR-021 guarantee the zero-chunk
        # path already has. `named`/`dominant`/`none` do not short-circuit; the decision is
        # carried forward and reused if the model ends up declining anyway.
        axis_decision: ProjectAxisDecision | None = None
        if settings.ek_f_enabled:
            named = named_project_codes(session, request.question)
            chunk_cards = available_from_chunks(by_id, chunks, limit=50)
            axis_decision = classify_project_axis(
                project_distribution(chunk_cards),
                named,
                disambig_spread=settings.project_axis_disambig_spread,
                dominant_share=settings.project_axis_dominant_share,
            )
            axis_decision = downgrade_existence_disambiguate(axis_decision, request.question)
        if axis_decision is not None and axis_decision.kind == "disambiguate":
            disambiguate_assist = build_disambiguate_assist(session, axis_decision)
            result = AskResult(
                answer=render_no_data(disambiguate_assist, request.question),
                answered=False,
                retrieved_document_ids=retrieved_ids,
                chunks=chunks,
                assist=disambiguate_assist,
            )
        else:
            now = temporal_today(settings)
            chain = evaluate_version_chains(documents, now)
            sources = answer_prompt.order_sources(chunks, by_id, chain)

            user_prompt = answer_prompt.build_user_prompt(
                request.question,
                sources,
                now,
                previous_question=request.previous_question if settings.ek_f_enabled else None,
            )
            try:
                response = llm.complete(
                    LLMRequest(
                        system=answer_prompt.system_prompt(settings.assist_computations),
                        user=user_prompt,
                        model=settings.llm_model_answer,
                        max_output_tokens=settings.llm_max_output_tokens,
                        reasoning_effort=settings.llm_reasoning_effort,
                    )
                )
            except LLMError as exc:
                if write_audit:
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
            # ADR-027: the model's optional `SORU:` line is separated first; the fixed
            # sentence is still canonicalised exactly as before (ADR-014).
            answer_text, model_question = (
                split_question_line(response.text)
                if settings.assist_computations
                else (response.text, None)
            )
            if answer_prompt.is_no_answer(answer_text):
                assist = (
                    build_insufficient_assist(
                        session,
                        allowed,
                        request.question,
                        documents=by_id,
                        chunks=chunks,
                        model_question=model_question,
                        ek_f=settings.ek_f_enabled,
                        axis_decision=axis_decision,
                        disambig_spread=settings.project_axis_disambig_spread,
                        dominant_share=settings.project_axis_dominant_share,
                    )
                    if settings.assist_computations
                    else None
                )
                shown = (
                    render_no_data(assist, request.question)
                    if settings.ek_f_enabled and assist is not None
                    else answer_prompt.NO_ANSWER_TEXT
                )
                result = AskResult(
                    answer=shown,
                    answered=False,
                    retrieved_document_ids=retrieved_ids,
                    model=response.model,
                    tokens_in=response.tokens_in,
                    tokens_out=response.tokens_out,
                    chunks=chunks,
                    assist=assist,
                )
            else:
                if model_question is not None:
                    # Rule 11 allows the line only on a no-answer; on an answered reply it
                    # is not shown (the answer carries its own citations).
                    log.info("assist question ignored on an answered reply")
                refs = answer_prompt.parse_citations(answer_text)
                cards, unknown = _source_cards(refs, sources)
                if unknown:
                    log.warning("unknown citation labels", extra={"labels": unknown})
                if not cards:
                    log.warning("answer without citations")
                if settings.ek_f_enabled:
                    # ADR-030 F-8 gate: dates and English number spellings only (SORU 8);
                    # citation labels were already read from the model's text above.
                    answer_text = polish_answer(answer_text)
                result = AskResult(
                    answer=answer_text.strip(),
                    answered=True,
                    sources=cards,
                    retrieved_document_ids=retrieved_ids,
                    model=response.model,
                    tokens_in=response.tokens_in,
                    tokens_out=response.tokens_out,
                    chunks=chunks,
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
    if write_audit:
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
            assist=result.assist,
            previous_question=request.previous_question if settings.ek_f_enabled else None,
        )
    return result
