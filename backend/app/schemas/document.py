from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus, IngestionStatus


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
    project_id: UUID | None
    external_ref: str | None
    created_at: datetime


class DocumentStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ingestion_status: IngestionStatus
    ingestion_error: str | None
    page_count: int | None
