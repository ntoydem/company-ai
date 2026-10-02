"""Per-company document-type guide (B-28b, BACKEND_GAPS §4.7.2, ADR-025): which extra fields
and tags usually matter for a family of documents. A *guide*, not a mandatory form — it steers
the classifier prompt and the upload screen; it never blocks a submission. Edited by the
customer admin; starter rows in `app/services/type_family.py`."""

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DocumentTypeGuide(Base):
    __tablename__ = "document_type_guide"

    family: Mapped[str] = mapped_column(String(32), primary_key=True)
    label: Mapped[str] = mapped_column(String(128))
    # lower-case substrings matched against `documents.document_type`
    type_patterns: Mapped[list[str]] = mapped_column(
        ARRAY(String(64)), default=list, server_default="{}"
    )
    # [{key, label, hint}]
    suggested_extra_fields: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, server_default="[]"
    )
    suggested_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(64)), default=list, server_default="{}"
    )
    standard_fields_emphasis: Mapped[list[str]] = mapped_column(
        ARRAY(String(64)), default=list, server_default="{}"
    )
    prompt_hint: Mapped[str] = mapped_column(Text, default="", server_default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
