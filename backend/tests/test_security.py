"""JWT access token helpers (`app/services/security.py`, Phase 1.1)."""

import time
import uuid

import jwt
import pytest

from app.models.user import UserRole
from app.services.security import (
    JWT_ALGORITHM,
    AccessTokenError,
    create_access_token,
    decode_access_token,
)

SECRET = "test-secret-at-least-32-bytes-long-for-hs256"


def test_create_and_decode_roundtrip() -> None:
    user_id = uuid.uuid4()
    token = create_access_token(
        user_id=user_id, role=UserRole.employee, secret=SECRET, expires_in_s=3600
    )

    assert decode_access_token(token, SECRET) == user_id


def test_decode_rejects_wrong_secret() -> None:
    token = create_access_token(
        user_id=uuid.uuid4(), role=UserRole.employee, secret=SECRET, expires_in_s=3600
    )

    with pytest.raises(AccessTokenError):
        decode_access_token(token, "different-secret")


def test_decode_rejects_expired_token() -> None:
    token = create_access_token(
        user_id=uuid.uuid4(), role=UserRole.employee, secret=SECRET, expires_in_s=-1
    )

    with pytest.raises(AccessTokenError):
        decode_access_token(token, SECRET)


def test_decode_rejects_malformed_token() -> None:
    with pytest.raises(AccessTokenError):
        decode_access_token("boyle-bir-token-yok", SECRET)


def test_decode_rejects_missing_sub_claim() -> None:
    token = jwt.encode(
        {"iat": time.time(), "exp": time.time() + 3600}, SECRET, algorithm=JWT_ALGORITHM
    )

    with pytest.raises(AccessTokenError):
        decode_access_token(token, SECRET)


def test_role_claim_is_not_authoritative_by_construction() -> None:
    """`decode_access_token` returns only the user id — callers cannot read a role out of
    it even if they wanted to, which forces the DB re-fetch (ADR-003: no refresh token)."""
    token = create_access_token(
        user_id=uuid.uuid4(), role=UserRole.admin, secret=SECRET, expires_in_s=3600
    )

    result = decode_access_token(token, SECRET)

    assert isinstance(result, uuid.UUID)
