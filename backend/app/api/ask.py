"""`POST /api/ask` — the one question entry point: router (ADR-010, Phase 4.3) →
document / Excel / mixed answer with page-level and cell-level sources."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_calculation_engine, get_current_user, get_llm_client, get_router
from app.core.config import Settings, get_settings
from app.core.db import get_session
from app.excel.calc import CalculationEngine
from app.models.user import User
from app.schemas.ask import AskRequest, AskResponse
from app.services.ask_router import answer_routed_question
from app.services.assist import assist_block
from app.services.llm import LLMClient
from app.services.pending_documents import pending_cards
from app.services.router import Router

router = APIRouter(prefix="/api/ask", tags=["ask"])


@router.post("", response_model=AskResponse)
def ask(
    body: AskRequest,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    current_user: Annotated[User, Depends(get_current_user)],
    llm: Annotated[LLMClient, Depends(get_llm_client)],
    engine: Annotated[CalculationEngine, Depends(get_calculation_engine)],
    question_router: Annotated[Router, Depends(get_router)],
) -> AskResponse:
    result = answer_routed_question(
        session, current_user, body, llm, settings, engine, question_router
    )
    return AskResponse(
        answer=result.answer,
        answered=result.answered,
        sources=result.sources,
        retrieved_document_ids=result.retrieved_document_ids,
        model=result.model,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        notice=result.notice,
        query_type=result.query_type,
        excel_sources=result.excel_sources,
        audit_log_id=result.audit_log_id,
        product_level=result.product_level,
        warnings=result.warnings,
        assist=assist_block(result.assist),
        pending_notice=result.pending.notice,
        pending_documents=pending_cards(result.pending),
    )
