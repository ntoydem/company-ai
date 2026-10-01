"""`GET /api/search` (B-14, Aşama D): content + metadata document hits inside the caller's
allowed set, projects and people in one response; no audit row."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.main import app
from app.models.project import Project, ProjectStage
from app.models.user import User, UserRole
from app.repositories import audit_log_repo, user_repo
from app.services.security import hash_password
from tests.department_fixtures import add_user_to_department, make_department
from tests.test_ask import _document


def test_search_requires_login_and_validates_params(client: TestClient, admin_user: User) -> None:
    app.dependency_overrides.pop(get_current_user, None)
    try:
        assert client.get("/api/search?q=dscr").status_code == 401
    finally:
        app.dependency_overrides[get_current_user] = lambda: admin_user
    assert client.get("/api/search").status_code == 422
    assert client.get("/api/search?q=d").status_code == 422
    assert client.get(f"/api/search?q={'x' * 201}").status_code == 422
    assert client.get("/api/search?q=dscr&limit=0").status_code == 422
    assert client.get("/api/search?q=dscr&limit=51").status_code == 422
    assert client.get("/api/search?q=hiçbirşeyyok").json() == {
        "documents": [],
        "projects": [],
        "people": [],
    }


def test_content_hits_carry_snippet_and_page_and_come_before_metadata_hits(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    covenant = _document(
        db_session,
        title="Facility Agreement",
        department=None,
        text="The Borrower shall maintain a minimum DSCR covenant of 1.20x.",
        page=5,
    )
    titled = _document(
        db_session, title="DSCR Policy Memo", department=None, text="Unrelated body text."
    )
    _document(db_session, title="Other", department=None, text="Nothing here.")

    body = client.get("/api/search?q=DSCR").json()
    docs = body["documents"]
    assert [d["id"] for d in docs] == [str(covenant.id), str(titled.id)]
    assert docs[0]["page_number"] == 5 and "DSCR" in docs[0]["snippet"]
    assert "<b>" not in docs[0]["snippet"]
    assert docs[1]["snippet"] is None and docs[1]["page_number"] is None
    assert docs[0]["file_kind"] == "pdf" and docs[0]["title"] == "Facility Agreement"
    assert audit_log_repo.list_filtered(db_session) == []  # search is not a question


def test_limit_caps_documents(client: TestClient, db_session: Session, admin_user: User) -> None:
    for i in range(4):
        _document(db_session, title=f"Doc {i}", department=None, text="covenant text here")
    assert len(client.get("/api/search?q=covenant&limit=2").json()["documents"]) == 2


def test_search_respects_allowed_document_ids(
    client: TestClient, db_session: Session, employee_user: User
) -> None:
    enerji = make_department(db_session, slug="enerji_grubu")
    make_department(db_session, slug="finans")
    add_user_to_department(db_session, employee_user, enerji)
    _document(db_session, title="Finans Covenant Report", department="finans", text="DSCR 1.37x")
    own = _document(db_session, title="Enerji Report", department="enerji_grubu", text="DSCR note")

    docs = client.get("/api/search?q=DSCR").json()["documents"]
    assert [d["id"] for d in docs] == [str(own.id)]  # content AND title of the finans doc hidden


def test_projects_and_people_match_name_code_and_title(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    db_session.add_all(
        [
            Project(name="Ankara RES", code="ANK_RES", stage=ProjectStage.operation),
            Project(name="İzmir RES", code="IZM_RES", stage=ProjectStage.development),
        ]
    )
    hukuk = make_department(db_session, slug="hukuk", name="Hukuk")
    musavir = user_repo.create(
        db_session,
        username="musavir",
        password_hash=hash_password("x"),
        display_name="Kemal Yıldız",
        role=UserRole.employee,
        title="Hukuk Müşaviri",
    )
    add_user_to_department(db_session, musavir, hukuk)
    db_session.commit()

    assert [p["code"] for p in client.get("/api/search?q=ank").json()["projects"]] == ["ANK_RES"]
    assert [p["code"] for p in client.get("/api/search?q=RES").json()["projects"]] == [
        "ANK_RES",
        "IZM_RES",
    ]
    people = client.get("/api/search?q=müşavir").json()["people"]
    assert [p["display_name"] for p in people] == ["Kemal Yıldız"]
    assert set(people[0]) == {"id", "display_name", "title", "department_slug", "department_name"}
