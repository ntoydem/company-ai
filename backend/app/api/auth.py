"""`POST /api/auth/login|logout`, `GET /api/auth/me` (SPEC_02 §7, ADR-003)."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_login_rate_limiter
from app.core.config import Settings, get_settings
from app.core.db import get_session
from app.models.user import User
from app.repositories import user_repo
from app.schemas.auth import CurrentUserResponse, LoginRequest
from app.services.rate_limit import LoginRateLimiter
from app.services.security import (
    ACCESS_TOKEN_COOKIE_NAME,
    create_access_token,
    verify_password,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

INVALID_CREDENTIALS_MESSAGE = "Kullanıcı adı veya şifre hatalı."
TOO_MANY_ATTEMPTS_MESSAGE = "Çok fazla başarısız giriş denemesi. Lütfen daha sonra tekrar deneyin."

ACCESS_TOKEN_MAX_AGE_S = 8 * 60 * 60  # 8 hours (SPEC_02 §7)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("/login", response_model=CurrentUserResponse)
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    rate_limiter: Annotated[LoginRateLimiter, Depends(get_login_rate_limiter)],
) -> CurrentUserResponse:
    client_ip = _client_ip(request)
    if rate_limiter.is_blocked(username=body.username, client_ip=client_ip):
        log.warning("login rate limited", extra={"username": body.username})
        raise HTTPException(429, TOO_MANY_ATTEMPTS_MESSAGE)

    user = user_repo.get_by_username(session, body.username)
    # Wrong username, wrong password and a disabled account all return the exact same
    # 401 — a different error for any one of them would let an attacker enumerate valid
    # usernames.
    if user is None or not verify_password(body.password, user.password_hash) or not user.is_active:
        rate_limiter.record_failure(username=body.username, client_ip=client_ip)
        log.warning("login failed", extra={"username": body.username})
        raise HTTPException(401, INVALID_CREDENTIALS_MESSAGE)

    rate_limiter.record_success(username=body.username)
    token = create_access_token(
        user_id=user.id,
        role=user.role,
        secret=settings.jwt_secret.get_secret_value(),
        expires_in_s=ACCESS_TOKEN_MAX_AGE_S,
    )
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=token,
        max_age=ACCESS_TOKEN_MAX_AGE_S,
        httponly=True,
        secure=False,  # V0: LAN, plain HTTP (ADR-015); flip to True once TLS lands
        samesite="lax",
        path="/",
    )
    log.info("login succeeded", extra={"username": user.username})
    return CurrentUserResponse.model_validate(user)


@router.post("/logout", status_code=204)
def logout(response: Response) -> None:
    """No auth dependency: a broken or expired cookie must still be clearable."""
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE_NAME, path="/")


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> CurrentUserResponse:
    return CurrentUserResponse.model_validate(current_user)
