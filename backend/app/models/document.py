import enum
import uuid
from datetime import date
from typing import Literal

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy import false as sa_false
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.project import Project

# B-13 (Aşama B): derived from `storage_path`'s extension, never stored — every upload is
# content-sniffed to one of pdf/png/jpg/xlsx/xlsm/csv (`api/documents.py::_detect_extension`)
# and written as `<uuid>/original.<ext>`, so the set is closed. `None` only for a
# hand-edited row with an extension outside it (no silent "pdf" guess).
FileKind = Literal["pdf", "image", "xlsx", "xlsm", "csv"]
_FILE_KIND_BY_EXTENSION: dict[str, FileKind] = {
    "pdf": "pdf",
    "png": "image",
    "jpg": "image",
    "jpeg": "image",
    "xlsx": "xlsx",
    "xlsm": "xlsm",
    "csv": "csv",
}


class DocumentStatus(enum.StrEnum):
    draft = "draft"
    executed = "executed"
    amended = "amended"
    superseded = "superseded"
    active = "active"


class Confidentiality(enum.StrEnum):
    normal = "normal"
    restricted = "restricted"
    board = "board"


class DocumentSource(enum.StrEnum):
    web = "web"
    consume = "consume"


class IngestionStatus(enum.StrEnum):
    uploaded = "uploaded"
    ocr = "ocr"
    ready = "ready"
    failed = "failed"


class Document(TimestampMixin, Base):
    """Master document metadata (SPEC_02 §2). `department` stays a denormalized slug
    string with no FK — existing rows/tests predate the `departments` table and use
    free-text department names; a misspelled slug fails safe by simply making the
    document invisible to everyone but admin, never by exposing it (see
    docs/plans/PHASE_1_2_PLAN.md T2). `project_id` has an FK to `projects.id` from
    Phase 1.2 onward."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    # Mandatory
    title: Mapped[str] = mapped_column(String(255))
    department: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    subdepartment: Mapped[str | None] = mapped_column(String(128), nullable=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # B-20/6 (Aşama D): the source card names the project without a second request from
    # the UI. Organisational only — permission still comes from `department` (ADR-004).
    project: Mapped[Project | None] = relationship("Project")
    # B-26 (Aşama E, ADR-023): the folder the document lives in; its `department` is the
    # folder owner's slug. NULL only for documents without a department (invisible to every
    # employee) or after their folder was deleted (SET NULL — folders with documents cannot
    # be deleted through the API, so this is a safety net, not a path).
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("folders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    document_type: Mapped[str] = mapped_column(String(64))
    counterparty: Mapped[str] = mapped_column(String(255))
    document_date: Mapped[date] = mapped_column(Date)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(
            DocumentStatus, name="document_status", values_callable=lambda e: [m.value for m in e]
        ),
        default=DocumentStatus.draft,
        index=True,
    )
    confidentiality: Mapped[Confidentiality] = mapped_column(
        Enum(
            Confidentiality,
            name="confidentiality_level",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=Confidentiality.normal,
    )
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(64)), default=list, server_default="{}")
    source: Mapped[DocumentSource] = mapped_column(
        Enum(
            DocumentSource, name="document_source", values_callable=lambda e: [m.value for m in e]
        ),
        default=DocumentSource.web,
    )

    # Temporal (ADR-012)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    revision: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    supersedes_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    superseded_by_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    related_document_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(Uuid), default=list, server_default="{}"
    )

    # System
    storage_path: Mapped[str] = mapped_column(String(512))
    ingestion_status: Mapped[IngestionStatus] = mapped_column(
        Enum(
            IngestionStatus, name="ingestion_status", values_callable=lambda e: [m.value for m in e]
        ),
        default=IngestionStatus.uploaded,
        index=True,
    )
    ingestion_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Deliberately FK-less (Phase 3.2, 0005_document_metadata_suggestions): a real FK to
    # `document_metadata_suggestions.id` would cycle with that table's own
    # `document_id -> documents.id` FK. Kept in sync only by
    # `app/services/metadata_suggestion.py`, used purely as an existence flag
    # ("has this document had a suggestion attempt yet") — actual lookups always go
    # through `document_metadata_suggestions.document_id`, never through this column.
    ai_suggestion_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Excel family only (Phase 4.2): the uploaded workbook carries a VBA project. Flagged
    # from the zip members at upload, shown in inspection — never loaded, never executed.
    has_macros: Mapped[bool] = mapped_column(Boolean, default=False, server_default=sa_false())
    # Original upload name ("Covenant_Report.xlsx"): what an Excel citation shows, since
    # `storage_path` is always <uuid>/original.<ext>. NULL for pre-4.2 rows.
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Truth-ledger document id (e.g. "DOC-ANK-FIN-004"), set only by the demo seed
    # (Phase 3.1); the upload API never sets this. Idempotency key for `make seed` and
    # the matching anchor for Phase 4.1's eval runner.
    external_ref: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)

    @property
    def storage_extension(self) -> str:
        return self.storage_path.rsplit(".", 1)[-1].lower() if "." in self.storage_path else ""

    @property
    def file_kind(self) -> FileKind | None:
        return _FILE_KIND_BY_EXTENSION.get(self.storage_extension)

    def __repr__(self) -> str:
        return f"Document(title={self.title!r}, ingestion_status={self.ingestion_status.value!r})"
