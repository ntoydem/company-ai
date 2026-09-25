"""`/api/excel/*` request/response shapes (Phase 4.2). `ExcelSourceCard` is deliberately a
separate type from the document `SourceCard`: file + sheet + range (SPEC_04 §5), no page."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

NO_INTERPRETATION_NOTICE = (
    "Bu cevap yorum içermez; hesabı DuckDB/Python yapar, yapay zeka yalnızca sonucu aktarır."
)


class ExcelAskRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    question: str = Field(min_length=3, max_length=1000)
    department: str | None = None
    project_id: UUID | None = None
    # Narrow to specific workbooks (still gated by allowed_document_ids).
    document_ids: list[UUID] | None = None


class ExcelSourceCard(BaseModel):
    model_config = ConfigDict(frozen=True)

    document_id: UUID | None
    file: str
    sheet: str
    range: str
    label: str  # "Covenant_Report.xlsx Q2_2026!D14"


class ExcelAskResponse(BaseModel):
    answer: str
    answered: bool
    value: float | int | str | None
    unit: str | None
    formatted_value: str | None
    sources: list[ExcelSourceCard]
    plan_kind: Literal["function", "sql", "none"]
    plan: dict[str, Any]
    excel_files: list[str]
    model: str | None
    tokens_in: int
    tokens_out: int
    notice: str = NO_INTERPRETATION_NOTICE


class SheetInfoResponse(BaseModel):
    name: str
    hidden: bool
    max_row: int
    max_col: int
    columns: list[str]


class NamedRangeResponse(BaseModel):
    name: str
    sheet: str
    ref: str


class WorkbookInspectResponse(BaseModel):
    document_id: UUID
    file: str
    kind: str
    sheets: list[SheetInfoResponse]
    named_ranges: list[NamedRangeResponse]
    has_macros: bool
    formula_cells: int
    formula_cells_without_cache: int
    needs_recalculation: bool
    tables: list[str]
