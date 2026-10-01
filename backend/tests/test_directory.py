"""`GET /api/directory` (B-05, Aşama C): everyone signed in may read it, it exposes exactly
five fields, and it filters by name/title and by department membership."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.repositories import user_repo
from app.services.security import hash_password
from tests.department_fixtures import add_user_to_department, make_department

FIELDS = {"id", "display_name", "title", "department_slug", "department_name"}


def _person(
    session: Session, username: str, display_name: str, *, title: str | None, active: bool = True
) -> User:
    user = user_repo.create(
        session,
        username=username,
        password_hash=hash_password("x"),
        display_name=display_name,
        role=UserRole.employee,
        title=title,
    )
    user.is_active = active
    session.commit()
    return user


def test_directory_requires_login(client: TestClient) -> None:
    assert client.get("/api/directory").status_code == 401


def test_directory_lists_active_people_with_five_fields_only(
    client: TestClient, db_session: Session, employee_user: User, management_user: User
) -> None:
    finans = make_department(db_session, slug="finans", name="Proje Finans")
    ayse = _person(db_session, "ayse", "Ayşe Demir", title="Proje Finans Uzmanı")
    add_user_to_department(db_session, ayse, finans)
    user_repo.update(db_session, ayse)  # resolves the primary department from memberships
    db_session.commit()
    _person(db_session, "eski", "Eski Çalışan", title=None, active=False)

    body = client.get("/api/directory").json()
    names = [p["display_name"] for p in body]
    assert "Ayşe Demir" in names and "Eski Çalışan" not in names
    assert "Test Yönetim" in names  # management is listed, with no department
    for person in body:
        assert set(person) == FIELDS, person
    ayse_row = next(p for p in body if p["display_name"] == "Ayşe Demir")
    assert ayse_row == {
        "id": str(ayse.id),
        "display_name": "Ayşe Demir",
        "title": "Proje Finans Uzmanı",
        "department_slug": "finans",
        "department_name": "Proje Finans",
    }
    yonetim_row = next(p for p in body if p["display_name"] == "Test Yönetim")
    assert yonetim_row["department_slug"] is None and yonetim_row["department_name"] is None


def test_directory_q_matches_name_or_title_and_department_filters_by_membership(
    client: TestClient, db_session: Session, employee_user: User
) -> None:
    hukuk = make_department(db_session, slug="hukuk", name="Hukuk")
    finans = make_department(db_session, slug="finans", name="Proje Finans")
    musavir = _person(db_session, "musavir", "Kemal Yıldız", title="Hukuk Müşaviri")
    add_user_to_department(db_session, musavir, hukuk)
    uzman = _person(db_session, "uzman", "Ayşe Demir", title="Proje Finans Uzmanı")
    add_user_to_department(db_session, uzman, finans)

    assert [p["display_name"] for p in client.get("/api/directory?q=müş").json()] == [
        "Kemal Yıldız"
    ]
    assert [p["display_name"] for p in client.get("/api/directory?q=ayşe").json()] == ["Ayşe Demir"]
    assert [p["display_name"] for p in client.get("/api/directory?department=finans").json()] == [
        "Ayşe Demir"
    ]
    assert client.get("/api/directory?department=yok-boyle-departman").json() == []
