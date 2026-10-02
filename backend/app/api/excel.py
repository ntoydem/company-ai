"""`POST /api/excel/ask` and `GET /api/excel/{document_id}/inspect` (Phase 4.2, SPEC_04).
DATA questions only; `/api/ask` reaches the same code through the router (Phase 4.3).
`/ask` computes, so it is a P2 capability (B-25); `/inspect` only reads and stays open in
P1 ("veri yükleyecek" covers workbooks — docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md §6.2)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import (
    get_calculation_engine,
    get_current_user,
    get_llm_client,
    require_product,
)
from app.core.config import Settings, get_settings
from app.core.db import get_session
from app.excel.calc import CalculationEngine, table_name
from app.excel.inspect import inspect_file
from app.models.user import User
from app.repositories import document_repo
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.authorization import AuthorizationScope
from app.schemas.excel import (
    ExcelAskRequest,
    ExcelAskResponse,
    NamedRangeResponse,
    SheetInfoResponse,
    WorkbookInspectResponse,
)
from app.services.authorization import allowed_document_ids
from app.services.excel_ask import answer_data_question
from app.services.llm import LLMClient

router = APIRouter(prefix="/api/excel", tags=["excel"])

DOCUMENT_NOT_FOUND_MESSAGE = "Belge bulunamadı."
NOT_A_WORKBOOK_MESSAGE = "Bu belge bir Excel/CSV dosyası değil."


@router.post("/ask", response_model=ExcelAskResponse)
def ask_excel(
    body: ExcelAskRequest,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    current_user: Annotated[User, Depends(get_current_user)],
    llm: Annotated[LLMClient, Depends(get_llm_client)],
    engine: Annotated[CalculationEngine, Depends(get_calculation_engine)],
    _p2: Annotated[None, Depends(require_product("P2"))],
) -> ExcelAskResponse:
    result = answer_data_question(session, current_user, body, llm, settings, engine)
    return ExcelAskResponse(
        answer=result.answer,
        answered=result.answered,
        value=result.value,
        unit=result.unit,
        formatted_value=result.formatted_value,
        sources=result.sources,
        plan_kind=result.plan_kind,
        plan=result.plan,
        excel_files=result.excel_files,
        model=result.model,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
    )


@router.get("/{document_id}/inspect", response_model=WorkbookInspectResponse)
def inspect_workbook(
    document_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> WorkbookInspectResponse:
    # B-28: the uploader inspects their own pending workbook too; `/ask` keeps the default
    # (approved-only) scope, so a pending workbook never enters a calculation.
    allowed = allowed_document_ids(
        current_user, AuthorizationScope(include_pending=True), SqlDocumentIdsProvider(session)
    )
    if document_id not in allowed:
        raise HTTPException(404, DOCUMENT_NOT_FOUND_MESSAGE)
    document = document_repo.get(session, document_id)
    if document is None:
        raise HTTPException(404, DOCUMENT_NOT_FOUND_MESSAGE)
    if not document.storage_path.lower().endswith(document_repo.EXCEL_SUFFIXES):
        raise HTTPException(422, NOT_A_WORKBOOK_MESSAGE)
    info = inspect_file(settings.documents_dir / document.storage_path)
    file_name = document.file_name or info.file
    return WorkbookInspectResponse(
        document_id=document.id,
        file=file_name,
        kind=info.kind,
        sheets=[
            SheetInfoResponse(
                name=s.name,
                hidden=s.hidden,
                max_row=s.max_row,
                max_col=s.max_col,
                columns=list(s.columns),
            )
            for s in info.sheets
        ],
        named_ranges=[
            NamedRangeResponse(name=n.name, sheet=n.sheet, ref=n.ref) for n in info.named_ranges
        ],
        has_macros=info.has_macros,
        formula_cells=info.formula_cells,
        formula_cells_without_cache=info.formula_cells_without_cache,
        needs_recalculation=info.needs_recalculation,
        tables=[table_name(file_name, s.name) for s in info.sheets if not s.hidden],
    )
