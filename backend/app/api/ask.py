"""`POST /api/ask` — document question answering with page-level sources (Phase 0.3)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_llm_client
from app.core.config import Settings, get_settings
from app.core.db import get_session
from app.models.user import User
from app.schemas.ask import AskRequest, AskResponse
from app.services.ask import answer_question
from app.services.llm import LLMClient

router = APIRouter(prefix="/api/ask", tags=["ask"])


@router.post("", response_model=AskResponse)
def ask(
    body: AskRequest,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    current_user: Annotated[User, Depends(get_current_user)],
    llm: Annotated[LLMClient, Depends(get_llm_client)],
) -> AskResponse:
    result = answer_question(session, current_user, body, llm, settings)
    return AskResponse(
        answer=result.answer,
        answered=result.answered,
        sources=result.sources,
        retrieved_document_ids=result.retrieved_document_ids,
        model=result.model,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
    )
