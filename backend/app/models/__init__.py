"""ORM models. Import every model here so Alembic autogenerate sees the full metadata."""

from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.department import Department
from app.models.document import (
    Confidentiality,
    Document,
    DocumentSource,
    DocumentStatus,
    IngestionStatus,
)
from app.models.document_chunk import DocumentChunk
from app.models.document_metadata_suggestion import DocumentMetadataSuggestion, SuggestionStatus
from app.models.document_page import DocumentPage
from app.models.ingestion_job import IngestionJob, IngestionJobStatus
from app.models.project import Project, ProjectStage
from app.models.project_department import ProjectDepartment
from app.models.user import User, UserRole
from app.models.user_department import UserDepartment

__all__ = [
    "AuditLog",
    "Base",
    "Confidentiality",
    "Department",
    "Document",
    "DocumentChunk",
    "DocumentMetadataSuggestion",
    "DocumentPage",
    "DocumentSource",
    "DocumentStatus",
    "IngestionJob",
    "IngestionJobStatus",
    "IngestionStatus",
    "Project",
    "ProjectDepartment",
    "ProjectStage",
    "SuggestionStatus",
    "User",
    "UserDepartment",
    "UserRole",
]
