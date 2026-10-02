"""Admin-only document intake/review ledger (B-28, BACKEND_GAPS §4.7.6, ADR-024)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.db import get_session
from app.models.user import User
from app.repositories import document_repo, document_review_repo
from app.schemas.document import ReviewEventResponse

router = APIRouter(prefix="/api/admin/documents", tags=["documents"])

DOCUMENT_NOT_FOUND_MESSAGE = "Belge bulunamadı."


@router.get("/{document_id}/review-events", response_model=list[ReviewEventResponse])
def list_review_events(
    document_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
    _admin: Annotated[User, Depends(require_admin)],
) -> list[ReviewEventResponse]:
    """What Balbal suggested, what the uploader changed/confirmed, who approved — oldest
    first. Admin sees every document (ADR-004), so no gate lookup is needed beyond
    existence; the ledger is never shown to regular users (§4.7.6)."""
    if document_repo.get(session, document_id) is None:
        raise HTTPException(404, DOCUMENT_NOT_FOUND_MESSAGE)
    return [
        ReviewEventResponse.model_validate(e)
        for e in document_review_repo.list_events(session, document_id)
    ]
