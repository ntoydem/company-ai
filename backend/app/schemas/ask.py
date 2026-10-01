from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.company_settings import ProductLevel
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

# Fixed warning texts (Tansu #1, docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md §5.3) —
# written by code, never by the model. `data_conflict` is deliberately absent: it needs a
# prompt change and its own eval category before the schema may promise it.
MISSING_DATA_WARNING = "Şirket kaynaklarında yeterli bilgi bulunamadı."
# Ç-7 "Yeterli Veri Bulunmamaktadır": documents were retrieved, the model still could not
# answer reliably — distinct from `missing_data` (nothing retrieved at all).
INSUFFICIENT_DATA_WARNING = (
    "Şirket kaynaklarında ilgili belgeler bulundu ancak soruyu güvenilir şekilde "
    "cevaplamaya yetmedi."
)
PRODUCT_LIMIT_WARNING = (
    "Bu özellik şirketinizin paketinde yok; soru yalnızca belgelerden cevaplandı."
)


class AskWarning(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["missing_data", "insufficient_data", "product_limit"]
    message: str
    # `request_data` = the B-11 "diğer departmandan bilgi talep et" button; the department
    # is picked by the user, never suggested by the system (kural 1).
    action: Literal["request_data"] | None = None


def missing_data_warning() -> AskWarning:
    return AskWarning(kind="missing_data", message=MISSING_DATA_WARNING, action="request_data")


def insufficient_data_warning() -> AskWarning:
    return AskWarning(
        kind="insufficient_data", message=INSUFFICIENT_DATA_WARNING, action="request_data"
    )


def product_limit_warning() -> AskWarning:
    return AskWarning(kind="product_limit", message=PRODUCT_LIMIT_WARNING)


class AskRequest(BaseModel):
    """`project_id` was removed 30.09.2026 (B-20/6, Aşama B): one conversation may span
    projects, the answer keeps them apart by citing sources. Pydantic's default
    `extra="ignore"` means an older client still sending it gets a normal answer, not a 422
    — the field is simply no longer a retrieval filter."""

    model_config = ConfigDict(frozen=True)

    question: str = Field(min_length=3, max_length=1000)
    department: str | None = None


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
    # B-07: the neighbour's id, so the UI can link to it. `None` when there is no
    # neighbour *or* the user may not see it — the chain is loaded through
    # `allowed_document_ids` at every hop (ADR-021), so a hidden link is never loaded.
    supersedes_document_id: UUID | None = None
    superseded_by_document_id: UUID | None = None
    # ADR-012 "İLK HALKA": the first link of its chain (already computed in code).
    is_initial: bool = False
    # B-20/6 (Aşama D): the document's project (P-6, every project shown apart); `None`
    # for project-less corporate documents. Not an authorization input (ADR-004).
    project_code: str | None = None
    project_name: str | None = None


class AskResponse(BaseModel):
    """Phase 4.3: `query_type`, `excel_sources` and a type-specific `notice` were added;
    `sources` keeps its Phase 0.3 meaning (document pages only) so older clients, the eval
    runner and the audit rows read the same. Aşama A (30.09.2026): `audit_log_id`,
    `product_level`, `warnings` — all additive."""

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
    # The audit row this answer wrote (ADR-016) — `None` only if that write failed.
    # Readable through the admin-only audit API alone; knowing the id grants nothing.
    audit_log_id: UUID | None = None
    product_level: ProductLevel = "P1"
    warnings: list[AskWarning] = Field(default_factory=list)
