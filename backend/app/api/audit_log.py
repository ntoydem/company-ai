"""`GET /api/audit-log` — admin-only, API only (SPEC_06 §1); the filtered admin UI on top
of this is Phase 5.2. Audit log is not corporate memory (ADR-016): read here, never by
retrieval or prompts."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.db import get_session
from app.models.user import User
from app.repositories import audit_log_repo
from app.schemas.audit_log import AuditLogDetail, AuditLogListItem

router = APIRouter(prefix="/api/audit-log", tags=["audit-log"])

AUDIT_LOG_NOT_FOUND_MESSAGE = "Audit log kaydı bulunamadı."


@router.get("", response_model=list[AuditLogListItem])
def list_audit_log(
    session: Annotated[Session, Depends(get_session)],
    _admin: Annotated[User, Depends(require_admin)],
    user_id: UUID | None = None,
    department: str | None = None,
    project_id: UUID | None = None,
    query_type: str | None = None,
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
    has_error: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AuditLogListItem]:
    rows = audit_log_repo.list_filtered(
        session,
        user_id=user_id,
        department=department,
        project_id=project_id,
        query_type=query_type,
        from_ts=from_ts,
        to_ts=to_ts,
        has_error=has_error,
        limit=limit,
        offset=offset,
    )
    return [AuditLogListItem.model_validate(row) for row in rows]


@router.get("/{audit_log_id}", response_model=AuditLogDetail)
def get_audit_log(
    session: Annotated[Session, Depends(get_session)],
    _admin: Annotated[User, Depends(require_admin)],
    audit_log_id: UUID,
) -> AuditLogDetail:
    row = audit_log_repo.get(session, audit_log_id)
    if row is None:
        raise HTTPException(404, AUDIT_LOG_NOT_FOUND_MESSAGE)
    return AuditLogDetail.model_validate(row)
