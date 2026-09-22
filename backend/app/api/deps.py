"""FastAPI dependencies shared across routers."""

from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.db import get_session
from app.models.user import User
from app.repositories import user_repo


def get_current_user(
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """Step-0 stand-in: always the seeded admin, mirroring `allowed_document_ids`'s own
    Step-0 stub (ADR-004). Replaced by a JWT-cookie dependency in Phase 1.1."""
    user = user_repo.get_by_username(session, settings.admin_username)
    if user is None:
        raise HTTPException(500, "Yönetici kullanıcı bulunamadı.")
    return user
