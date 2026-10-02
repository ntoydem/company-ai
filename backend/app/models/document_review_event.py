"""Append-only intake/review ledger for one document (B-28, BACKEND_GAPS §4.7.6, ADR-024).

What Balbal suggested and how sure it was, what the uploader changed or confirmed, who
approved or sent the document back and when. Not `audit_log` — that table records questions
(ADR-016). Read by admins only (§4.7.6: "kullanıcı ekranında görünmez").
"""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ReviewEventKind(enum.StrEnum):
    uploaded = "uploaded"
    auto_approved = "auto_approved"
    field_edited = "field_edited"  # uploader wrote a value different from the suggestion
    field_confirmed = "field_confirmed"  # uploader explicitly confirmed a low-confidence value
    submitted = "submitted"
    resubmitted = "resubmitted"
    approved = "approved"
    changes_requested = "changes_requested"
    metadata_changed_after_approval = "metadata_changed_after_approval"


class DocumentReviewEvent(Base):
    __tablename__ = "document_review_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    # Python-side timestamp: several events are written in one request/transaction, and
    # `now()` would give them all the same value — the ledger must read back in order.
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
    kind: Mapped[ReviewEventKind] = mapped_column(
        Enum(
            ReviewEventKind,
            name="document_review_event_kind",
            values_callable=lambda e: [m.value for m in e],
        )
    )
    field: Mapped[str | None] = mapped_column(String(64), nullable=True)
    before: Mapped[str | None] = mapped_column(Text, nullable=True)
    after: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"DocumentReviewEvent(document_id={self.document_id!r}, kind={self.kind.value!r})"
