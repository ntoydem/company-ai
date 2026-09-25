"""`/api/ask` orchestration (ADR-010, Phase 4.3): route → run the matching pipeline(s)
unchanged → merge deterministically → one audit row.

- DOCUMENT → `ask.answer_question` as before.
- DATA → `excel_ask.answer_data_question` (the same code `/api/excel/ask` runs).
- MIXED → both, with the router's two sub-questions; the two answers are concatenated
  under fixed headings — no third LLM call, no interpretation (SPEC_04 §8 "yorum yok").
  Both branches always run; if one finds nothing its fixed "not found" text stays in place
  so the model never silently picks a side (plan §4).
- GENERAL → `general_answer.answer_general`: no retrieval, no workbook, no
  `allowed_document_ids` call at all.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.excel.calc import CalculationEngine
from app.models.user import User
from app.repositories import project_repo
from app.repositories.document_chunk_repo import RetrievedChunk
from app.schemas.ask import (
    GENERAL_NOTICE,
    MIXED_NOTICE,
    NO_INTERPRETATION_NOTICE,
    AskRequest,
    QueryType,
    SourceCard,
)
from app.schemas.excel import NO_INTERPRETATION_NOTICE as EXCEL_NOTICE
from app.schemas.excel import ExcelAskRequest, ExcelSourceCard
from app.services.ask import answer_question
from app.services.audit_writer import write_audit_row
from app.services.excel_ask import answer_data_question, excel_document_ids
from app.services.general_answer import answer_general
from app.services.llm import LLMClient, LLMError
from app.services.router import RoutedQuestion, Router

log = logging.getLogger(__name__)

DOCUMENT_PART_HEADING = "Belgelere göre:"
DATA_PART_HEADING = "Excel verisine göre:"

NOTICE_BY_TYPE: dict[str, str] = {
    "DOCUMENT_QUERY": NO_INTERPRETATION_NOTICE,
    "DATA_QUERY": EXCEL_NOTICE,
    "MIXED_QUERY": MIXED_NOTICE,
    "GENERAL_QUERY": GENERAL_NOTICE,
}


@dataclass(frozen=True)
class RoutedAnswer:
    query_type: QueryType
    answer: str
    answered: bool
    notice: str
    sources: list[SourceCard] = field(default_factory=list)
    excel_sources: list[ExcelSourceCard] = field(default_factory=list)
    retrieved_document_ids: list[UUID] = field(default_factory=list)
    chunks: list[RetrievedChunk] = field(default_factory=list)
    model: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0


def merge_mixed_answer(document_answer: str, data_answer: str) -> str:
    return (
        f"{DOCUMENT_PART_HEADING}\n{document_answer.strip()}\n\n"
        f"{DATA_PART_HEADING}\n{data_answer.strip()}"
    )


def _run(
    session: Session,
    user: User,
    request: AskRequest,
    routed: RoutedQuestion,
    llm: LLMClient,
    settings: Settings,
    engine: CalculationEngine,
) -> RoutedAnswer:
    query_type = routed.query_type
    notice = NOTICE_BY_TYPE[query_type]

    if query_type == "GENERAL_QUERY":
        project_names = [p.name for p in project_repo.list_all(session)]
        general = answer_general(request.question, llm, settings, forbidden_terms=project_names)
        return RoutedAnswer(
            query_type=query_type,
            answer=general.answer,
            answered=general.answered,
            notice=notice,
            model=general.model,
            tokens_in=general.tokens_in,
            tokens_out=general.tokens_out,
        )

    doc = data = None
    if routed.document_question is not None:
        doc = answer_question(
            session,
            user,
            AskRequest(
                question=routed.document_question,
                department=request.department,
                project_id=request.project_id,
            ),
            llm,
            settings,
            write_audit=False,
        )
    if routed.data_question is not None:
        data = answer_data_question(
            session,
            user,
            ExcelAskRequest(
                question=routed.data_question,
                department=request.department,
                project_id=request.project_id,
            ),
            llm,
            settings,
            engine,
            write_audit=False,
        )

    if query_type == "DATA_QUERY" and data is not None and not data.answered:
        # A DATA miss (no visible workbook, plan `none`, unknown period …) falls through
        # to the document pipeline with the original question: a question the router
        # mis-tagged as DATA — "yerli banka kredisi ne kadar?" is an amount *stated* in a
        # contract — then behaves exactly as before the router, instead of ending in an
        # "Excel'de bulamadım" dead end (Phase 4.3 eval finding). The audit row records
        # the path actually taken.
        log.info("data miss, falling back to documents", extra={"reason": data.answer})
        query_type, notice = "DOCUMENT_QUERY", NOTICE_BY_TYPE["DOCUMENT_QUERY"]
        doc = answer_question(session, user, request, llm, settings, write_audit=False)
        data = None

    if doc is not None and data is not None:
        answer = merge_mixed_answer(doc.answer, data.answer)
        answered = doc.answered or data.answered
    elif doc is not None:
        answer, answered = doc.answer, doc.answered
    else:
        assert data is not None
        answer, answered = data.answer, data.answered

    sources = doc.sources if doc else []
    excel_sources = data.sources if data else []
    retrieved = list(doc.retrieved_document_ids) if doc else []
    retrieved += [i for i in excel_document_ids(excel_sources) if i not in retrieved]
    return RoutedAnswer(
        query_type=query_type,
        answer=answer,
        answered=answered,
        notice=notice,
        sources=sources,
        excel_sources=excel_sources,
        retrieved_document_ids=retrieved,
        chunks=doc.chunks if doc else [],
        model=(doc.model if doc else None) or (data.model if data else None),
        tokens_in=(doc.tokens_in if doc else 0) + (data.tokens_in if data else 0),
        tokens_out=(doc.tokens_out if doc else 0) + (data.tokens_out if data else 0),
    )


def answer_routed_question(
    session: Session,
    user: User,
    request: AskRequest,
    llm: LLMClient,
    settings: Settings,
    engine: CalculationEngine,
    router: Router,
) -> RoutedAnswer:
    """One `/api/ask` call: route, run, write the single audit row (SORU 2). On an LLM
    failure the row is written with `error` and the exception propagates (→ 503, as
    before)."""
    started = time.perf_counter()
    routed = router.route(request.question)

    def elapsed_ms() -> int:
        return round((time.perf_counter() - started) * 1000)

    try:
        result = _run(session, user, request, routed, llm, settings, engine)
    except LLMError as exc:
        write_audit_row(
            session,
            user,
            question=request.question,
            query_type=routed.query_type,
            scope_department=request.department,
            scope_project=request.project_id,
            documents_retrieved=[],
            chunks=[],
            answer="",
            sources=[],
            excel_sources=[],
            model=None,
            tokens_in=routed.tokens_in,
            tokens_out=routed.tokens_out,
            execution_ms=elapsed_ms(),
            error=str(exc),
        )
        raise

    tokens_in = result.tokens_in + routed.tokens_in
    tokens_out = result.tokens_out + routed.tokens_out
    log.info(
        "ask routed",
        extra={
            "user_id": str(user.id),
            "query_type": result.query_type,
            "answered": result.answered,
            "document_sources": len(result.sources),
            "excel_sources": len(result.excel_sources),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "duration_ms": elapsed_ms(),
        },
    )
    write_audit_row(
        session,
        user,
        question=request.question,
        query_type=result.query_type,
        scope_department=request.department,
        scope_project=request.project_id,
        documents_retrieved=result.retrieved_document_ids,
        chunks=result.chunks,
        answer=result.answer,
        sources=result.sources,
        excel_sources=result.excel_sources,
        model=result.model or routed.model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        execution_ms=elapsed_ms(),
        error=None,
    )
    return RoutedAnswer(
        query_type=result.query_type,
        answer=result.answer,
        answered=result.answered,
        notice=result.notice,
        sources=result.sources,
        excel_sources=result.excel_sources,
        retrieved_document_ids=result.retrieved_document_ids,
        chunks=result.chunks,
        model=result.model or routed.model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
    )
