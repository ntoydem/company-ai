import uuid

from sqlalchemy.orm import Session

from app.models.user import UserRole
from app.repositories import user_repo
from app.services.security import hash_password


def test_get_by_id_returns_matching_user(db_session: Session) -> None:
    created = user_repo.create(
        db_session,
        username="test-kullanici",
        password_hash=hash_password("sifre"),
        display_name="Test Kullanıcı",
        role=UserRole.employee,
    )
    db_session.commit()

    found = user_repo.get_by_id(db_session, created.id)

    assert found is not None
    assert found.id == created.id
    assert found.username == "test-kullanici"


def test_get_by_id_returns_none_when_missing(db_session: Session) -> None:
    assert user_repo.get_by_id(db_session, uuid.uuid4()) is None
