from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogListItem(BaseModel):
    """Lightweight row for `GET /api/audit-log` (admin-only) — no `answer`/`sources`,
    which can be large; use `GET /api/audit-log/{id}` for the full record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    timestamp: datetime
    user_id: UUID | None
    question: str
    query_type: str
    scope_department: str | None
    scope_project: UUID | None
    model: str | None
    tokens_in: int
    tokens_out: int
    execution_ms: int
    error: str | None


class AuditLogDetail(AuditLogListItem):
    documents_retrieved: list[UUID]
    chunks_retrieved: list[dict[str, Any]]
    excel_files_used: list[str]
    answer: str
    sources: list[dict[str, Any]]
    cost_estimate: Decimal | None
    request_id: str | None
    product_level: str | None
    warnings: list[dict[str, Any]]
    # ADR-027: the assist block the user saw (None when ASSIST_MODE was off / answered).
    assist: dict[str, Any] | None = None
