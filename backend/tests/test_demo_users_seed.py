from pydantic import SecretStr
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.user import UserRole
from app.repositories import user_repo
from app.services.demo_users_seed import ensure_demo_users
from app.services.security import verify_password

_EXPECTED_ROLES = {
    "yonetim": UserRole.management,
    "finans": UserRole.employee,
    "hukuk": UserRole.employee,
    "enerji": UserRole.employee,
}


def test_first_run_creates_all_demo_users_with_expected_roles(
    db_session: Session, settings: Settings
) -> None:
    results = ensure_demo_users(db_session, settings)

    assert {r.username for r in results} == set(_EXPECTED_ROLES)
    assert all(r.created for r in results)
    for username, role in _EXPECTED_ROLES.items():
        user = user_repo.get_by_username(db_session, username)
        assert user is not None
        assert user.role == role
        assert user.is_active is True
        assert user.password_hash.startswith("$argon2id$")
        assert verify_password(settings.demo_user_password.get_secret_value(), user.password_hash)


def test_second_run_is_idempotent_and_never_changes_password(
    db_session: Session, settings: Settings
) -> None:
    ensure_demo_users(db_session, settings)
    original = user_repo.get_by_username(db_session, "finans")
    assert original is not None
    original_hash = original.password_hash

    changed = settings.model_copy(update={"demo_user_password": SecretStr("baska-bir-sifre")})
    results = ensure_demo_users(db_session, changed)

    assert all(r.created is False for r in results)
    db_session.expire_all()
    again = user_repo.get_by_username(db_session, "finans")
    assert again is not None
    assert again.password_hash == original_hash


def test_demo_users_carry_titles_and_finans_is_proje_finans(
    db_session: Session, settings: Settings
) -> None:
    ensure_demo_users(db_session, settings)
    finans = user_repo.get_by_username(db_session, "finans")
    hukuk = user_repo.get_by_username(db_session, "hukuk")
    assert finans is not None and hukuk is not None
    assert (finans.display_name, finans.title) == ("Proje Finans", "Proje Finans Uzmanı")
    assert hukuk.title == "Hukuk Müşaviri"
