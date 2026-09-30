"""FastAPI dependencies shared across routers."""

from collections.abc import Callable
from functools import lru_cache
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.db import get_session
from app.core.errors import NOT_AUTHENTICATED_MESSAGE, NOT_AUTHORIZED_MESSAGE
from app.excel.calc import CachedValueEngine, CalculationEngine
from app.models.company_settings import ProductLevel
from app.models.user import User, UserRole
from app.repositories import company_settings_repo, user_repo
from app.services.llm import LLMClient, build_llm_client
from app.services.rate_limit import LoginRateLimiter
from app.services.router import LLMRouter, Router
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


def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Gate for admin-only endpoints (Phase 1.2, e.g. project CRUD)."""
    if current_user.role != UserRole.admin:
        raise HTTPException(403, NOT_AUTHORIZED_MESSAGE)
    return current_user


# Machine-readable, not a Turkish sentence: the contract with the AI-BalBal frontend
# (BAGLANTI_YOL_HARITASI.md §2.1/3), which renders its own text for a closed layer.
PRODUCT_NOT_ENABLED_DETAIL = "product_not_enabled"


def require_product(level: ProductLevel) -> Callable[..., None]:
    """Gate for endpoints that belong to a product layer (B-25, ADR-022). Authentication
    runs first (401 before 403); the layer is read from `company_settings` per request."""

    def dependency(
        session: Annotated[Session, Depends(get_session)],
        _user: Annotated[User, Depends(get_current_user)],
    ) -> None:
        if level not in company_settings_repo.enabled_products(session):
            raise HTTPException(403, PRODUCT_NOT_ENABLED_DETAIL)

    return dependency


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


@lru_cache
def _cached_calculation_engine() -> CalculationEngine:
    settings = get_settings()
    return CachedValueEngine(
        timeout_s=settings.excel_query_timeout_s, row_limit=settings.excel_row_limit
    )


def get_calculation_engine() -> CalculationEngine:
    """Phase 4.2 (ADR-011): the one `CalculationEngine` implementation, `CachedValueEngine`.
    Stateless apart from its limits, so a process-wide instance is fine."""
    return _cached_calculation_engine()


def get_router(
    llm: Annotated[LLMClient, Depends(get_llm_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Router:
    """Phase 4.3 (ADR-010): the question router. Tests override this with a `FakeRouter`
    so `/api/ask` branches are exercised without a classification call."""
    return LLMRouter(llm, settings)
