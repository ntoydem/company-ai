import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditLog(Base):
    """Who asked what, when, with which scope, which sources were used (SPEC_06 §1).

    Not corporate memory (ADR-016): never read by retrieval or prompts, admin-only,
    90-day retention. No `TimestampMixin` — a row is written once and never updated;
    `timestamp` is the event time, not a bookkeeping column.
    """

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # FK + SET NULL, same as Document.uploaded_by_id / DocumentMetadataSuggestion.applied_by_id
    # — the row survives a deleted user, only the pointer clears.
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    question: Mapped[str] = mapped_column(Text)
    # Always "DOCUMENT_QUERY" until the router (ADR-010) lands in Phase 4.3.
    query_type: Mapped[str] = mapped_column(String(32), default="DOCUMENT_QUERY")
    scope_department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    scope_project: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    documents_retrieved: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(Uuid), default=list, server_default="{}"
    )
    # Always [] until the Excel engine (Phase 4.2).
    excel_files_used: Mapped[list[str]] = mapped_column(
        ARRAY(String(255)), default=list, server_default="{}"
    )
    # (document_id, page_number, rank) of every chunk that reached the prompt — page
    # level, unlike `documents_retrieved`; lets a retrieval miss be told apart from a
    # model refusal after the fact (Phase 3.2b).
    chunks_retrieved: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, server_default="[]"
    )
    answer: Mapped[str] = mapped_column(Text)
    sources: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tokens_in: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    tokens_out: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    # USD; NULL when the model has no known price — never a guessed number.
    cost_estimate: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    execution_ms: Mapped[int] = mapped_column(Integer)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # System/LLM failure only — "no source found" is a normal outcome, not an error.
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Product layer the answer was produced in (B-25) and the structured warnings the
    # user saw (missing_data / product_limit) — stored, not derived, so a later change to
    # the query_type→product mapping never rewrites history. NULL / [] before migration 0009.
    product_level: Mapped[str | None] = mapped_column(String(2), nullable=True)
    warnings: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, server_default="[]")

    def __repr__(self) -> str:
        return f"AuditLog(user_id={self.user_id!r}, timestamp={self.timestamp!r})"
