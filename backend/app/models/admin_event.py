"""Append-only ledger of customer-admin configuration changes (B-28b, ADR-025): tag catalogue,
document-type guide — and, from here on, the place for role/membership changes (B-08 SORU 2).
Not `audit_log` (ADR-016 records questions) and not `document_review_events` (per document)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AdminEvent(Base):
    __tablename__ = "admin_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    actor_name: Mapped[str] = mapped_column(String(128))
    # tag_created | tag_updated | guide_created | guide_updated | (later) role_changed, …
    kind: Mapped[str] = mapped_column(String(32), index=True)
    # tag slug, guide family, username …
    target: Mapped[str] = mapped_column(String(128))
    before: Mapped[str | None] = mapped_column(Text, nullable=True)
    after: Mapped[str | None] = mapped_column(Text, nullable=True)
