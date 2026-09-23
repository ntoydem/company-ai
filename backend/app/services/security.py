"""Auth cryptography: password hashing (Argon2id) and access tokens (JWT)."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.models.user import UserRole

_hasher = PasswordHasher()


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, plain)
    except VerifyMismatchError:
        return False


JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_COOKIE_NAME = "access_token"


class AccessTokenError(Exception):
    """Token missing, expired, malformed, or signed with a different secret.

    Named distinctly from PyJWT's own `jwt.InvalidTokenError` to avoid confusion between
    the two exception hierarchies.
    """


def create_access_token(
    *, user_id: uuid.UUID, role: UserRole, secret: str, expires_in_s: int
) -> str:
    """`role` is carried only for observability (e.g. reading a decoded token by hand);
    it is never authoritative for an authorization decision — see `decode_access_token`."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in_s),
    }
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str, secret: str) -> uuid.UUID:
    """Returns the user id from the `sub` claim.

    Callers must re-fetch the `User` row from the database and use its current `role`/
    `is_active` — there is no refresh or revocation mechanism (ADR-003), so a promoted,
    demoted or deactivated user must take effect on the next request, not wait for the
    token to expire.
    """
    try:
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        return uuid.UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise AccessTokenError("invalid access token") from exc
