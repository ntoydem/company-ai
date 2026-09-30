"""`audit_log` persistence (SPEC_06 §1, Phase 3.4). Written once per `/api/ask` call,
read only by the admin-only API (`app/api/audit_log.py`) — never by retrieval or
prompts (ADR-016: audit log is not corporate memory).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def create(
    session: Session,
    *,
    user_id: uuid.UUID | None,
    question: str,
    query_type: str,
    scope_department: str | None,
    scope_project: uuid.UUID | None,
    documents_retrieved: list[uuid.UUID],
    answer: str,
    sources: list[dict[str, Any]],
    model: str | None,
    tokens_in: int,
    tokens_out: int,
    cost_estimate: Decimal | None,
    execution_ms: int,
    request_id: str | None,
    error: str | None,
    excel_files_used: list[str] | None = None,
    chunks_retrieved: list[dict[str, Any]] | None = None,
    product_level: str | None = None,
    warnings: list[dict[str, Any]] | None = None,
) -> AuditLog:
    row = AuditLog(
        user_id=user_id,
        question=question,
        query_type=query_type,
        scope_department=scope_department,
        scope_project=scope_project,
        documents_retrieved=documents_retrieved,
        chunks_retrieved=chunks_retrieved or [],
        excel_files_used=excel_files_used or [],
        answer=answer,
        sources=sources,
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_estimate=cost_estimate,
        execution_ms=execution_ms,
        request_id=request_id,
        error=error,
        product_level=product_level,
        warnings=warnings or [],
    )
    session.add(row)
    session.commit()
    return row


def get(session: Session, audit_log_id: uuid.UUID) -> AuditLog | None:
    return session.get(AuditLog, audit_log_id)


def get_by_request_id(session: Session, request_id: str) -> AuditLog | None:
    return session.scalar(select(AuditLog).where(AuditLog.request_id == request_id))


def list_filtered(
    session: Session,
    *,
    user_id: uuid.UUID | None = None,
    department: str | None = None,
    project_id: uuid.UUID | None = None,
    query_type: str | None = None,
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
    has_error: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[AuditLog]:
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc())
    if user_id is not None:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if department is not None:
        stmt = stmt.where(AuditLog.scope_department == department)
    if project_id is not None:
        stmt = stmt.where(AuditLog.scope_project == project_id)
    if query_type is not None:
        stmt = stmt.where(AuditLog.query_type == query_type)
    if from_ts is not None:
        stmt = stmt.where(AuditLog.timestamp >= from_ts)
    if to_ts is not None:
        stmt = stmt.where(AuditLog.timestamp <= to_ts)
    if has_error is True:
        stmt = stmt.where(AuditLog.error.is_not(None))
    elif has_error is False:
        stmt = stmt.where(AuditLog.error.is_(None))
    stmt = stmt.limit(limit).offset(offset)
    return list(session.scalars(stmt).all())


def delete_older_than(session: Session, cutoff: datetime) -> int:
    """Phase 3.4 daily cleanup (SPEC_06 §1: 90-day retention). Returns rows deleted."""
    result = cast(
        "CursorResult[Any]", session.execute(delete(AuditLog).where(AuditLog.timestamp < cutoff))
    )
    session.commit()
    return result.rowcount
