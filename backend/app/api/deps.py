"""FastAPI dependencies shared across routers."""

from functools import lru_cache
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.db import get_session
from app.core.errors import NOT_AUTHENTICATED_MESSAGE
from app.models.user import User
from app.repositories import user_repo
from app.services.llm import LLMClient, build_llm_client
from app.services.rate_limit import LoginRateLimiter
from app.services.security import ACCESS_TOKEN_COOKIE_NAME, AccessTokenError, decode_access_token


def get_current_user(
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    access_token: Annotated[str | None, Cookie(alias=ACCESS_TOKEN_COOKIE_NAME)] = None,
) -> User:
    if access_token is None:
        raise HTTPException(401, NOT_AUTHENTICATED_MESSAGE)
    try:
        user_id = decode_access_token(access_token, settings.jwt_secret.get_secret_value())
    except AccessTokenError:
        raise HTTPException(401, NOT_AUTHENTICATED_MESSAGE) from None
    user = user_repo.get_by_id(session, user_id)
    if user is None or not user.is_active:
        raise HTTPException(401, NOT_AUTHENTICATED_MESSAGE)
    return user


@lru_cache
def _cached_llm_client() -> LLMClient:
    return build_llm_client(get_settings())


def get_llm_client() -> LLMClient:
    """One client per process. Raises `LLMNotConfiguredError` (→ 503) when no key is set,
    so the rest of the API keeps working without an LLM (SPEC_06 §8). Tests override this
    dependency with a fake."""
    return _cached_llm_client()


@lru_cache
def _login_rate_limiter() -> LoginRateLimiter:
    return LoginRateLimiter()


def get_login_rate_limiter() -> LoginRateLimiter:
    """One limiter per process (ADR-015); resets on restart, acceptable for V0."""
    return _login_rate_limiter()
