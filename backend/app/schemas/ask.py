from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.document import DocumentStatus
from app.schemas.excel import ExcelSourceCard

# ADR-010. Stored verbatim in `audit_log.query_type`. GENERAL_QUERY (general-knowledge
# answers with no company source) was removed 30.09.2026 — the system must never again
# answer from the model's own world knowledge; every question, including definitions,
# is checked against the documents first (see `services/router.py`'s module docstring).
QueryType = Literal["DOCUMENT_QUERY", "DATA_QUERY", "MIXED_QUERY"]

NO_INTERPRETATION_NOTICE = (
    "Bu cevap yorum içermez; yalnızca şirket belgelerinde yazanı kaynak göstererek aktarır."
)
MIXED_NOTICE = (
    "Bu cevap yorum içermez; belge kısmı kaynak göstererek aktarılır, Excel kısmının hesabını "
    "DuckDB/Python yapar. İki kısım birleştirilmiş, yorumlanmamıştır."
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
    """Phase 4.3: `query_type`, `excel_sources` and a type-specific `notice` were added;
    `sources` keeps its Phase 0.3 meaning (document pages only) so older clients, the eval
    runner and the audit rows read the same."""

    answer: str
    answered: bool
    sources: list[SourceCard]
    retrieved_document_ids: list[UUID]
    model: str | None
    tokens_in: int
    tokens_out: int
    notice: str = NO_INTERPRETATION_NOTICE
    query_type: QueryType = "DOCUMENT_QUERY"
    excel_sources: list[ExcelSourceCard] = Field(default_factory=list)
