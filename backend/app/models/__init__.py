"""ORM models. Import every model here so Alembic autogenerate sees the full metadata."""

from app.models.base import Base
from app.models.document import (
    Confidentiality,
    Document,
    DocumentSource,
    DocumentStatus,
    IngestionStatus,
)
from app.models.document_chunk import DocumentChunk
from app.models.document_page import DocumentPage
from app.models.ingestion_job import IngestionJob, IngestionJobStatus
from app.models.user import User, UserRole

__all__ = [
    "Base",
    "Confidentiality",
    "Document",
    "DocumentChunk",
    "DocumentPage",
    "DocumentSource",
    "DocumentStatus",
    "IngestionJob",
    "IngestionJobStatus",
    "IngestionStatus",
    "User",
    "UserRole",
]
