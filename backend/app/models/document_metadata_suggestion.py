import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class SuggestionStatus(enum.StrEnum):
    pending = "pending"
    applied = "applied"
    rejected = "rejected"
    failed = "failed"


class DocumentMetadataSuggestion(TimestampMixin, Base):
    """AI-proposed metadata for one document (SPEC_02 §4). One row per document
    (`document_id` unique) — a retry after `failed` needs an explicit new call, not a
    history table; V0 does not need suggestion history.

    `fields` is a JSONB map of `{field_name: {"value": ..., "confidence": 0.0-1.0}}` for
    `department, subdepartment, project_code, document_type, counterparty, document_date,
    status, confidentiality, tags`. `project_code` (not `project_id`) because the model
    only ever sees `projects.code` strings, never UUIDs; the accept endpoint resolves it.
    Nothing here ever changes `documents` until `POST .../apply` — SPEC_02 §4's "kritik
    alan sessiz overwrite yok" is satisfied by that endpoint requiring explicit field
    values, not by anything in this model.
    """

    __tablename__ = "document_metadata_suggestions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), unique=True, index=True
    )
    model: Mapped[str] = mapped_column(String(64))
    status: Mapped[SuggestionStatus] = mapped_column(
        Enum(
            SuggestionStatus,
            name="suggestion_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=SuggestionStatus.pending,
    )
    fields: Mapped[dict[str, Any]] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    applied_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"DocumentMetadataSuggestion(document_id={self.document_id!r}, "
            f"status={self.status.value!r})"
        )
