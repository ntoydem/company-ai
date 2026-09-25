from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.document import Confidentiality, DocumentStatus, IngestionStatus
from app.models.document_metadata_suggestion import SuggestionStatus


class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ingestion_status: IngestionStatus


class DocumentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    document_type: str
    counterparty: str
    document_date: date
    status: DocumentStatus
    ingestion_status: IngestionStatus
    department: str | None
    subdepartment: str | None
    project_id: UUID | None
    confidentiality: Confidentiality
    external_ref: str | None
    created_at: datetime


class DocumentDetailResponse(DocumentListItem):
    """`GET /api/documents/{id}` (Phase 3.3, SORU 1): the list item plus the temporal and
    system fields a detail/review screen needs."""

    tags: list[str]
    effective_date: date | None
    expiration_date: date | None
    version: int
    supersedes_document_id: UUID | None
    superseded_by_document_id: UUID | None
    related_document_ids: list[UUID]
    ingestion_error: str | None
    page_count: int | None
    has_macros: bool


class DocumentStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ingestion_status: IngestionStatus
    ingestion_error: str | None
    page_count: int | None


class MetadataSuggestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    model: str
    status: SuggestionStatus
    fields: dict[str, Any]
    error: str | None
    applied_at: datetime | None
    applied_by_id: UUID | None


class MetadataSuggestionApplyRequest(BaseModel):
    """Only the fields present here are written to the document (SPEC_02 §4: no field
    changes without an explicit value in this request — "kritik alan sessiz overwrite
    yok" applies uniformly, not just to a subset of fields)."""

    department: str | None = None
    subdepartment: str | None = None
    project_code: str | None = None
    document_type: str | None = None
    counterparty: str | None = None
    document_date: date | None = None
    status: DocumentStatus | None = None
    confidentiality: Confidentiality | None = None
    tags: list[str] | None = None
