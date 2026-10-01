from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.document import Confidentiality, DocumentStatus, FileKind, IngestionStatus
from app.models.document_metadata_suggestion import SuggestionStatus
from app.models.user import UserRole


class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ingestion_status: IngestionStatus
    file_kind: FileKind | None


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
    # B-13: pdf | image | xlsx | xlsm | csv, derived from the stored file (Document.file_kind).
    file_kind: FileKind | None
    # B-26: the folder the document lives in (null = no department / legacy).
    folder_id: UUID | None


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


class DocumentMetadataEditRequest(BaseModel):
    """Manual admin edit (Phase 5.2, SORU 1), independent of the AI-suggestion flow —
    same 9 fields as `MetadataSuggestionApplyRequest` plus `title`/`effective_date`/
    `expiration_date`. Version-chain fields (`supersedes_document_id` etc.) are
    intentionally not exposed here (ADR-012: chain edits must go through the linking
    checks in the upload/apply flows, never a silent overwrite)."""

    title: str | None = None
    department: str | None = None
    subdepartment: str | None = None
    project_code: str | None = None
    document_type: str | None = None
    counterparty: str | None = None
    document_date: date | None = None
    status: DocumentStatus | None = None
    confidentiality: Confidentiality | None = None
    tags: list[str] | None = None
    effective_date: date | None = None
    expiration_date: date | None = None


class DocumentVisibilityUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    display_name: str
    role: UserRole


class DocumentVisibilityResponse(BaseModel):
    """`GET /api/documents/{id}/visibility` (Phase 5.2, "bu belgeyi kim görebilir")."""

    document_id: UUID
    department: str | None
    confidentiality: Confidentiality
    users: list[DocumentVisibilityUser]
