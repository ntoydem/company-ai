"""One `audit_log` row per `/api/ask` (or `/api/excel/ask`) call — the single write path
shared by the document pipeline, the Excel pipeline and the router (Phase 4.3, SORU 2:
a MIXED question is still *one* call and therefore one row). Never raises: a logging
failure must not break the answer the user already has (ADR-006 pattern)."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.request_id import get_request_id
from app.models.user import User
from app.repositories import audit_log_repo
from app.repositories.document_chunk_repo import RetrievedChunk
from app.schemas.ask import AskWarning, SourceCard
from app.schemas.excel import ExcelSourceCard
from app.services import pending_documents
from app.services.assist import Assist, assist_json

log = logging.getLogger(__name__)


def source_cards_json(
    sources: list[SourceCard], excel_sources: list[ExcelSourceCard]
) -> list[dict[str, Any]]:
    """`sources` JSONB: every card carries `kind` so the admin API can tell a document
    page (`document`) from a workbook range (`excel`) once both sit in one row."""
    return [{"kind": "document", **card.model_dump(mode="json")} for card in sources] + [
        {"kind": "excel", **card.model_dump(mode="json")} for card in excel_sources
    ]


def chunks_json(chunks: list[RetrievedChunk]) -> list[dict[str, Any]]:
    return [
        {"document_id": str(c.document_id), "page_number": c.page_number, "rank": c.rank}
        for c in chunks
    ]


def write_audit_row(
    session: Session,
    user: User,
    *,
    question: str,
    query_type: str,
    scope_department: str | None,
    scope_project: UUID | None,
    documents_retrieved: list[UUID],
    chunks: list[RetrievedChunk],
    answer: str,
    sources: list[SourceCard],
    excel_sources: list[ExcelSourceCard],
    model: str | None,
    tokens_in: int,
    tokens_out: int,
    execution_ms: int,
    error: str | None,
    product_level: str | None = None,
    warnings: list[AskWarning] | None = None,
    assist: Assist | None = None,
    pending: pending_documents.PendingOutcome | None = None,
) -> UUID | None:
    """SPEC_06 §1. `cost_estimate` stays `NULL` in V0 — no invented per-model pricing
    (Phase 3.2 SORU 2). Returns the new row's id (`AskResponse.audit_log_id`), or `None`
    when the write failed — the answer is still returned."""
    try:
        row = audit_log_repo.create(
            session,
            user_id=user.id,
            question=question,
            query_type=query_type,
            scope_department=scope_department,
            scope_project=scope_project,
            documents_retrieved=documents_retrieved,
            chunks_retrieved=chunks_json(chunks),
            answer=answer,
            sources=source_cards_json(sources, excel_sources),
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_estimate=None,
            execution_ms=execution_ms,
            request_id=get_request_id(),
            error=error,
            excel_files_used=sorted({card.file for card in excel_sources}),
            product_level=product_level,
            warnings=[w.model_dump(mode="json") for w in warnings or []],
            assist=pending_documents.audit_json(assist_json(assist), pending),
        )
    except Exception:
        log.exception("audit log write failed")
        return None
    return row.id
