from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.document import (
    Confidentiality,
    DocumentReviewStatus,
    DocumentStatus,
    FileKind,
    IngestionStatus,
)
from app.models.document_metadata_suggestion import SuggestionStatus
from app.models.document_review_event import ReviewEventKind
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
    # B-28: publication state; only `approved` documents reach search/Balbal.
    review_status: DocumentReviewStatus


class ExtraFieldValue(BaseModel):
    """One `documents.extra_fields` entry (B-28b): who recorded it and how sure Balbal was."""

    value: str
    source: Literal["ai", "user"] = "user"
    confidence: float | None = None
    added_by_id: UUID | None = None
    added_at: datetime | None = None


class DocumentDetailResponse(DocumentListItem):
    """`GET /api/documents/{id}` (Phase 3.3, SORU 1): the list item plus the temporal and
    system fields a detail/review screen needs."""

    tags: list[str]
    # B-28 review trail (the full ledger is admin-only, `/api/admin/documents/{id}/review-events`).
    # `uploaded_by_id` lets the UI show "Onaya gönder" only to the uploader (the server still
    # enforces it, 403 `not_the_uploader`) — AI-BalBal PR-2.
    uploaded_by_id: UUID | None
    # B-28b: type-specific facts (staff/AI), string values only.
    extra_fields: dict[str, ExtraFieldValue]
    review_comment: str | None
    submitted_at: datetime | None
    reviewed_at: datetime | None
    reviewed_by_id: UUID | None
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
    # B-28b: key → value; `null` removes the key. Keys are normalised to snake_case.
    extra_fields: dict[str, str | None] | None = None


class DocumentSubmitRequest(MetadataSuggestionApplyRequest):
    """B-28 stage 1 (`POST /api/documents/{id}/submit`): the uploader's final metadata — the
    same nine fields as the apply request — plus the fields whose low-confidence suggestion
    they explicitly confirm (BACKEND_GAPS §4.7.5 "Onaylıyorum" box). Only fields present are
    written; a kept low-confidence value that is not confirmed is refused (422)."""

    confirmed_fields: list[str] = Field(default_factory=list)


class DocumentReviewRequest(BaseModel):
    """B-28 stage 2 (`POST /api/documents/{id}/review`), by the target department's
    `department_manager`. `request_changes` needs a comment — the uploader must know what
    to fix."""

    decision: Literal["approve", "request_changes"]
    comment: str | None = Field(default=None, max_length=2000)


class ReviewEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    created_at: datetime
    actor_name: str
    kind: ReviewEventKind
    field: str | None
    before: str | None
    after: str | None
    confidence: float | None
    comment: str | None


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
    extra_fields: dict[str, str | None] | None = None
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
    # B-28: for a pending document the list is who can *handle* it (uploader, target
    # department's manager, admin), not who will see it once approved.
    review_status: DocumentReviewStatus
    users: list[DocumentVisibilityUser]
