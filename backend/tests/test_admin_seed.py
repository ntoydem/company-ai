from pydantic import SecretStr
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.user import UserRole
from app.repositories import user_repo
from app.services.admin_seed import ensure_admin_user
from app.services.security import verify_password


def test_first_run_creates_admin_with_argon2_hash(db_session: Session, settings: Settings) -> None:
    result = ensure_admin_user(db_session, settings)
    assert result.created is True

    user = user_repo.get_by_username(db_session, settings.admin_username)
    assert user is not None
    assert user.role == UserRole.admin
    assert user.is_active is True
    assert user.auth_provider == "local"
    assert user.password_hash.startswith("$argon2id$")
    plain = settings.admin_password.get_secret_value()
    assert user.password_hash != plain
    assert verify_password(plain, user.password_hash)
    assert not verify_password(plain + "x", user.password_hash)


def test_second_run_is_idempotent_and_never_changes_password(
    db_session: Session, settings: Settings
) -> None:
    ensure_admin_user(db_session, settings)
    first_hash = user_repo.get_by_username(db_session, settings.admin_username)
    assert first_hash is not None
    original = first_hash.password_hash

    changed = settings.model_copy(update={"admin_password": SecretStr("another-password")})
    result = ensure_admin_user(db_session, changed)
    assert result.created is False

    db_session.expire_all()
    again = user_repo.get_by_username(db_session, settings.admin_username)
    assert again is not None
    assert again.password_hash == original
