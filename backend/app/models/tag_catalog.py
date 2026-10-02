"""Company tag catalogue (B-28b, BACKEND_GAPS §4.7.4, ADR-025).

Tags come from a fixed, company-managed list so the same event is always tagged the same way;
the list grows only by a human (customer admin) decision. `identity` tags name company / subject /
type; `change` tags mark what an amendment alters. Retired tags are deactivated, never deleted
(older documents keep referencing them).
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TagKind(enum.StrEnum):
    identity = "identity"
    change = "change"


class TagCatalog(Base):
    __tablename__ = "tag_catalog"

    slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(128))
    kind: Mapped[TagKind] = mapped_column(
        Enum(TagKind, name="tag_kind", values_callable=lambda e: [m.value for m in e]),
        default=TagKind.identity,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
