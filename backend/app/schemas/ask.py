from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.document import DocumentStatus

NO_INTERPRETATION_NOTICE = (
    "Bu cevap yorum içermez; yalnızca şirket belgelerinde yazanı kaynak göstererek aktarır."
)


class AskRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    question: str = Field(min_length=3, max_length=1000)
    department: str | None = None
    project_id: UUID | None = None


class SourceCard(BaseModel):
    """One cited (document, page) pair — what the user (and the audit log) sees (ADR-008)."""

    model_config = ConfigDict(frozen=True)

    ref: str
    document_id: UUID
    title: str
    page_number: int
    document_date: date
    effective_date: date | None
    version: int
    status: DocumentStatus
    is_current: bool
    supersedes_title: str | None
    superseded_by_title: str | None


class AskResponse(BaseModel):
    answer: str
    answered: bool
    sources: list[SourceCard]
    retrieved_document_ids: list[UUID]
    model: str | None
    tokens_in: int
    tokens_out: int
    notice: str = NO_INTERPRETATION_NOTICE
