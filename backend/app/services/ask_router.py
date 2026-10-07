"""`/api/ask` orchestration (ADR-010, Phase 4.3): route → run the matching pipeline(s)
unchanged → merge deterministically → one audit row.

- DOCUMENT → `ask.answer_question` as before.
- DATA → `excel_ask.answer_data_question` (the same code `/api/excel/ask` runs).
- MIXED → both, with the router's two sub-questions; the two answers are concatenated
  under fixed headings — no third LLM call, no interpretation (SPEC_04 §8 "yorum yok").
  Both branches always run; if one finds nothing its fixed "not found" text stays in place
  so the model never silently picks a side (plan §4).

GENERAL_QUERY (general-knowledge answers with no company source) was removed 30.09.2026 —
see `router.py`'s module docstring.

Aşama A (30.09.2026, B-25): the product layer of an answer is a function of its *final*
query type (`PRODUCT_LEVEL_BY_TYPE`). When P2 is not enabled, a DATA/MIXED routing is
degraded to DOCUMENT with the original question — the safe direction of ADR-010 — and the
answer carries a `product_limit` warning instead of a refusal.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.excel.calc import CalculationEngine
from app.models.company_settings import ProductLevel
from app.models.user import User
from app.repositories import company_settings_repo
from app.repositories.document_chunk_repo import RetrievedChunk
from app.schemas.ask import (
    MIXED_NOTICE,
    NO_INTERPRETATION_NOTICE,
    AskRequest,
    AskWarning,
    QueryType,
    SourceCard,
    document_processing_warning,
    document_unreadable_warning,
    insufficient_data_warning,
    missing_data_warning,
    product_limit_warning,
)
from app.schemas.excel import NO_INTERPRETATION_NOTICE as EXCEL_NOTICE
from app.schemas.excel import ExcelAskRequest, ExcelSourceCard
from app.services import pending_documents
from app.services.ask import answer_question
from app.services.assist import Assist
from app.services.audit_writer import write_audit_row
from app.services.excel_ask import answer_data_question, excel_document_ids
from app.services.llm import LLMClient, LLMError
from app.services.router import RoutedQuestion, Router

log = logging.getLogger(__name__)

DOCUMENT_PART_HEADING = "Belgelere göre:"
DATA_PART_HEADING = "Excel verisine göre:"

NOTICE_BY_TYPE: dict[str, str] = {
    "DOCUMENT_QUERY": NO_INTERPRETATION_NOTICE,
    "DATA_QUERY": EXCEL_NOTICE,
    "MIXED_QUERY": MIXED_NOTICE,
}

# docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md §6.1 — the mapping lives in code, not in a
# table: which layer a capability belongs to is a property of the system.
PRODUCT_LEVEL_BY_TYPE: dict[QueryType, ProductLevel] = {
    "DOCUMENT_QUERY": "P1",
    "DATA_QUERY": "P2",
    "MIXED_QUERY": "P2",
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
    product_level: ProductLevel = "P1"
    warnings: list[AskWarning] = field(default_factory=list)
    audit_log_id: UUID | None = None
    # ADR-027: the document pipeline's assist block (None when off / answered / DATA-only).
    assist: Assist | None = None
    # Tansu Not 7 §3: state A/B/C of "a matching document is still processing" (NO_PENDING
    # when off / DATA-only / state D). Computed after the answer, never shown to the model.
    pending: pending_documents.PendingOutcome = pending_documents.NO_PENDING


def merge_mixed_answer(document_answer: str, data_answer: str) -> str:
    return (
        f"{DOCUMENT_PART_HEADING}\n{document_answer.strip()}\n\n"
        f"{DATA_PART_HEADING}\n{data_answer.strip()}"
    )


def degrade_for_products(
    routed: RoutedQuestion, enabled_products: list[ProductLevel], question: str
) -> tuple[RoutedQuestion, list[AskWarning]]:
    """P2 closed + router chose a computing branch → answer from documents only, with the
    original question (the router's DOCUMENT/DATA branches always run the original
    question anyway), and say so in a fixed warning. The request is never refused."""
    if routed.query_type == "DOCUMENT_QUERY" or "P2" in enabled_products:
        return routed, []
    degraded = RoutedQuestion(
        query_type="DOCUMENT_QUERY",
        document_question=question,
        data_question=None,
        reason=f"product_limit: {routed.query_type} needs P2",
        model=routed.model,
        tokens_in=routed.tokens_in,
        tokens_out=routed.tokens_out,
    )
    return degraded, [product_limit_warning()]


def _run(
    session: Session,
    user: User,
    request: AskRequest,
    routed: RoutedQuestion,
    llm: LLMClient,
    settings: Settings,
    engine: CalculationEngine,
    warnings: list[AskWarning],
) -> RoutedAnswer:
    query_type = routed.query_type
    notice = NOTICE_BY_TYPE[query_type]

    doc = data = None
    if routed.document_question is not None:
        doc = answer_question(
            session,
            user,
            AskRequest(question=routed.document_question, department=request.department),
            llm,
            settings,
            write_audit=False,
            # Adım 2: code-side ambiguity check only on the pure DOCUMENT path (a MIXED
            # question legitimately spans a contract value and a report value).
            check_ambiguity=query_type == "DOCUMENT_QUERY",
        )
    if routed.data_question is not None:
        data = answer_data_question(
            session,
            user,
            ExcelAskRequest(question=routed.data_question, department=request.department),
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
    pending = pending_documents.NO_PENDING
    if settings.assist_mode_enabled and doc is not None:
        # Not 7 §3, after the answer and without the LLM: did a document the user can
        # already see in their list, but Balbal cannot read yet, match the question?
        pending = pending_documents.evaluate(
            session,
            user,
            request.department,
            request.question,
            answered=answered,
            retrieved=doc.retrieved_document_ids,
        )
    if not answered:
        # Ç-7: documents reached the prompt but the model said they do not suffice →
        # "yeterli veri bulunmamaktadır"; nothing retrieved at all → "veri yok". The Excel
        # branch's own miss (no workbook / plan none) stays `missing_data` this round.
        # Not 7 states A/B replace that label: the ready documents were searched and hold
        # nothing, while a matching document is still processing / unreadable.
        if pending.state == "A":
            no_answer = [document_processing_warning(pending_documents.PROCESSED_NOTE)]
        elif pending.state == "B":
            no_answer = [document_unreadable_warning(pending_documents.PROCESSED_NOTE)]
        else:
            no_answer = [
                insufficient_data_warning()
                if doc is not None and doc.retrieved_document_ids
                else missing_data_warning()
            ]
    else:
        no_answer = []
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
        product_level=PRODUCT_LEVEL_BY_TYPE[query_type],
        warnings=warnings + no_answer,
        assist=doc.assist if (doc is not None and not answered) else None,
        pending=pending,
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
    enabled_products = company_settings_repo.enabled_products(session)
    routed, warnings = degrade_for_products(
        router.route(request.question), enabled_products, request.question
    )

    def elapsed_ms() -> int:
        return round((time.perf_counter() - started) * 1000)

    try:
        result = _run(session, user, request, routed, llm, settings, engine, warnings)
    except LLMError as exc:
        write_audit_row(
            session,
            user,
            question=request.question,
            query_type=routed.query_type,
            scope_department=request.department,
            scope_project=None,
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
            product_level=PRODUCT_LEVEL_BY_TYPE[routed.query_type],
            warnings=warnings,
        )
        raise

    tokens_in = result.tokens_in + routed.tokens_in
    tokens_out = result.tokens_out + routed.tokens_out
    log.info(
        "ask routed",
        extra={
            "user_id": str(user.id),
            "query_type": result.query_type,
            "product_level": result.product_level,
            "warnings": [w.kind for w in result.warnings],
            "answered": result.answered,
            "document_sources": len(result.sources),
            "excel_sources": len(result.excel_sources),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "duration_ms": elapsed_ms(),
        },
    )
    audit_log_id = write_audit_row(
        session,
        user,
        question=request.question,
        query_type=result.query_type,
        scope_department=request.department,
        scope_project=None,
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
        product_level=result.product_level,
        warnings=result.warnings,
        assist=result.assist,
        pending=result.pending,
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
        product_level=result.product_level,
        warnings=result.warnings,
        audit_log_id=audit_log_id,
        assist=result.assist,
        pending=result.pending,
    )
