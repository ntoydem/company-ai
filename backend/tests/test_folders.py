"""Folders and department access grants (B-26, ADR-023, Aşama E) — BACKEND_GAPS §2.6.5
acceptance tests end to end: grants feed the one gate (`allowed_document_ids`), so a read
grant shows a document in the list, in search, in Balbal's retrieval and on download;
revoking it hides the document everywhere in the very next request; folder access never
exceeds confidentiality; every effective change is one event."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import Settings
from app.main import app
from app.models.department import Department
from app.models.document import Confidentiality
from app.models.project import Project, ProjectStage
from app.models.user import User, UserRole
from app.repositories import folder_repo, user_repo
from app.services.security import hash_password
from tests.department_fixtures import add_user_to_department, make_department
from tests.fakes import FakeLLMClient
from tests.test_ask import _ask, _document
from tests.test_documents import FAKE_PDF, _document_with_file

ADMIN_FOLDER_KEYS = {"id", "name", "parent_id", "owner_department_slug", "grants", "document_count"}
GRANT_KEYS = {"department_slug", "access", "inherited"}
USER_FOLDER_KEYS = {"id", "name", "parent_id", "owner_department_slug", "access", "document_count"}
AUDIT_KEYS = {
    "id",
    "created_at",
    "actor_name",
    "folder_id",
    "folder_name",
    "department_slug",
    "before",
    "after",
}


@contextmanager
def _as(user: User) -> Iterator[None]:
    previous = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        yield
    finally:
        if previous is not None:
            app.dependency_overrides[get_current_user] = previous
        else:
            app.dependency_overrides.pop(get_current_user, None)


def _employee(session: Session, username: str, department: Department) -> User:
    user = user_repo.create(
        session,
        username=username,
        password_hash=hash_password("x"),
        display_name=username.title(),
        role=UserRole.employee,
    )
    add_user_to_department(session, user, department)
    return user


def _folder(client: TestClient, name: str, owner: str, parent_id: str | None = None) -> dict:
    response = client.post(
        "/api/admin/folders",
        json={"name": name, "parent_id": parent_id, "owner_department_slug": owner},
    )
    assert response.status_code == 201, response.text
    body: dict = response.json()
    return body


def _grant(client: TestClient, folder_id: str, department_slug: str, access: str) -> dict:
    response = client.put(
        f"/api/admin/folders/{folder_id}/grants",
        json={"grants": [{"department_slug": department_slug, "access": access}]},
    )
    assert response.status_code == 200, response.text
    body: dict = response.json()
    return body


def _visible_ids(client: TestClient) -> set[str]:
    return {row["id"] for row in client.get("/api/documents").json()}


def _search_ids(client: TestClient, q: str) -> set[str]:
    return {row["id"] for row in client.get(f"/api/search?q={q}").json()["documents"]}


def _setup(db_session: Session, settings: Settings) -> tuple[Department, Department, User]:
    hukuk = make_department(db_session, slug="hukuk", name="Hukuk")
    finans = make_department(db_session, slug="finans", name="Proje Finans")
    finans_user = _employee(db_session, "finans-calisan", finans)
    folder_repo.create(db_session, name="Hukuk", parent_id=None, owner_department=hukuk)
    folder_repo.create(db_session, name="Proje Finans", parent_id=None, owner_department=finans)
    db_session.commit()
    return hukuk, finans, finans_user


# ---------------------------------------------------------------- E-01 / E-03 / E-09


def test_read_grant_shows_documents_everywhere_and_revocation_hides_them_at_once(
    client: TestClient,
    db_session: Session,
    settings: Settings,
    admin_user: User,
    fake_llm: FakeLLMClient,
) -> None:
    hukuk, _finans, finans_user = _setup(db_session, settings)
    contracts = _folder(client, "Proje Sözleşmeleri", "hukuk", parent_id=None)
    contracts_id = uuid.UUID(contracts["id"])
    # One document with text (retrieval/search) and one with a real file (download).
    text_doc = _document(
        db_session,
        title="Ankara RES Kredi Sözleşmesi",
        department="hukuk",
        text="DSCR covenant 1,20x",
    )
    file_doc = _document_with_file(db_session, settings, department="hukuk", title="Sözleşme")
    text_doc.folder_id = file_doc.folder_id = contracts_id
    db_session.commit()
    fake_llm.replies = ["Covenant 1,20x [K1]."] * 3

    # Before any grant: a Proje Finans employee sees nothing of Hukuk's folder.
    with _as(finans_user):
        assert _visible_ids(client) == set()
        assert client.get(f"/api/documents/{file_doc.id}/download").status_code == 403
        assert _search_ids(client, "covenant") == set()
        body = _ask(client, "DSCR covenant nedir?")
        assert body["answered"] is False and fake_llm.requests == []

    # (1) read grant → list, search, Balbal retrieval, download; upload still 403.
    _grant(client, contracts["id"], "finans", "read")
    with _as(finans_user):
        assert _visible_ids(client) == {str(text_doc.id), str(file_doc.id)}
        response = client.get(f"/api/documents/{file_doc.id}/download")
        assert response.status_code == 200 and response.content == FAKE_PDF
        assert _search_ids(client, "covenant") == {str(text_doc.id)}
        body = _ask(client, "DSCR covenant nedir?")
        assert body["answered"] is True and str(text_doc.id) in body["retrieved_document_ids"]
        assert "Ankara RES Kredi Sözleşmesi" in fake_llm.requests[-1].user
        upload = client.post(
            "/api/documents/upload",
            files={"file": ("x.pdf", FAKE_PDF, "application/pdf")},
            data={
                "title": "Yeni",
                "document_type": "t",
                "document_date": "2026-01-01",
                "counterparty": "c",
                "folder_id": contracts["id"],
            },
        )
        assert upload.status_code == 403
    requests_after_grant = len(fake_llm.requests)
    # (9) "kim görebilir" agrees with the grant.
    visible_users = {
        u["username"]
        for u in client.get(f"/api/documents/{text_doc.id}/visibility").json()["users"]
    }
    assert finans_user.username in visible_users

    # (3) revoke → gone everywhere in the next request, no caching anywhere.
    _grant(client, contracts["id"], "finans", "none")
    with _as(finans_user):
        assert _visible_ids(client) == set()
        assert client.get(f"/api/documents/{file_doc.id}/download").status_code == 403
        assert _search_ids(client, "covenant") == set()
        body = _ask(client, "DSCR covenant nedir?")
        assert body["answered"] is False and body["retrieved_document_ids"] == []
        assert len(fake_llm.requests) == requests_after_grant  # zero chunks → no LLM call
    visible_users = {
        u["username"]
        for u in client.get(f"/api/documents/{text_doc.id}/visibility").json()["users"]
    }
    assert finans_user.username not in visible_users
    assert hukuk.slug == "hukuk"


# ---------------------------------------------------------------- E-02 / E-13


def test_write_grant_allows_upload_and_new_version_with_department_derived_from_folder(
    client: TestClient, db_session: Session, settings: Settings, admin_user: User
) -> None:
    _hukuk, _finans, finans_user = _setup(db_session, settings)
    contracts = _folder(client, "Proje Sözleşmeleri", "hukuk")
    _grant(client, contracts["id"], "finans", "write")

    def upload(**extra: str) -> object:
        return client.post(
            "/api/documents/upload",
            files={"file": ("x.pdf", FAKE_PDF, "application/pdf")},
            data={
                "title": "Sözleşme",
                "document_type": "t",
                "document_date": "2026-01-01",
                "counterparty": "c",
                **extra,
            },
        )

    with _as(finans_user):
        first = upload(folder_id=contracts["id"])
        assert first.status_code == 201, first.text
        detail = client.get(f"/api/documents/{first.json()['id']}").json()
        assert detail["department"] == "hukuk" and detail["folder_id"] == contracts["id"]
        assert first.json()["id"] in _visible_ids(client)  # the uploader sees it via the grant
        # New version in the same folder.
        second = upload(
            folder_id=contracts["id"], supersedes_document_id=first.json()["id"], version="2"
        )
        assert second.status_code == 201, second.text
        # Department contradicting the folder owner → 422.
        assert upload(folder_id=contracts["id"], department="finans").status_code == 422
    # (13) No folder_id: an admin upload with only a department lands in that root folder.
    root = client.post(
        "/api/documents/upload",
        files={"file": ("x.pdf", FAKE_PDF, "application/pdf")},
        data={
            "title": "Kök",
            "document_type": "t",
            "document_date": "2026-01-01",
            "counterparty": "c",
            "department": "hukuk",
        },
    ).json()
    hukuk_root = next(
        f
        for f in client.get("/api/admin/folders").json()
        if f["name"] == "Hukuk" and f["parent_id"] is None
    )
    assert client.get(f"/api/documents/{root['id']}").json()["folder_id"] == hukuk_root["id"]
    # No folder and no department → no folder either (legacy path).
    bare = client.post(
        "/api/documents/upload",
        files={"file": ("x.pdf", FAKE_PDF, "application/pdf")},
        data={
            "title": "Yok",
            "document_type": "t",
            "document_date": "2026-01-01",
            "counterparty": "c",
        },
    ).json()
    assert client.get(f"/api/documents/{bare['id']}").json()["folder_id"] is None


# ---------------------------------------------------------------- E-04


def test_inheritance_and_child_override(
    client: TestClient, db_session: Session, settings: Settings, admin_user: User
) -> None:
    _hukuk, _finans, finans_user = _setup(db_session, settings)
    contracts = _folder(client, "Proje Sözleşmeleri", "hukuk")
    ankara = _folder(client, "Ankara RES", "hukuk", parent_id=contracts["id"])
    doc = _document(db_session, title="Alt klasör belgesi", department="hukuk", text="x")
    doc.folder_id = uuid.UUID(ankara["id"])
    db_session.commit()

    def upload_to(folder_id: str) -> int:
        return client.post(
            "/api/documents/upload",
            files={"file": ("x.pdf", FAKE_PDF, "application/pdf")},
            data={
                "title": "t",
                "document_type": "t",
                "document_date": "2026-01-01",
                "counterparty": "c",
                "folder_id": folder_id,
            },
        ).status_code

    _grant(client, contracts["id"], "finans", "read")  # parent: read
    folders = {f["name"]: f for f in client.get("/api/admin/folders").json()}
    assert folders["Ankara RES"]["grants"] == [
        {"department_slug": "finans", "access": "read", "inherited": True}
    ]
    with _as(finans_user):
        assert str(doc.id) in _visible_ids(client)  # inherited read
        assert upload_to(ankara["id"]) == 403 and upload_to(contracts["id"]) == 403

    _grant(client, ankara["id"], "finans", "write")  # child: write overrides
    folders = {f["name"]: f for f in client.get("/api/admin/folders").json()}
    assert folders["Ankara RES"]["grants"] == [
        {"department_slug": "finans", "access": "write", "inherited": False}
    ]
    with _as(finans_user):
        assert upload_to(ankara["id"]) == 201 and upload_to(contracts["id"]) == 403
        mine = {f["name"]: f["access"] for f in client.get("/api/folders").json()}
        assert mine["Proje Sözleşmeleri"] == "read" and mine["Ankara RES"] == "write"

    _grant(client, ankara["id"], "finans", "none")  # drop the override → parent's read again
    with _as(finans_user):
        assert str(doc.id) in _visible_ids(client)
        assert upload_to(ankara["id"]) == 403


# ---------------------------------------------------------------- E-05 / E-06


def test_folder_grant_never_exceeds_confidentiality_and_applies_to_every_project(
    client: TestClient,
    db_session: Session,
    settings: Settings,
    admin_user: User,
) -> None:
    _hukuk, _finans, finans_user = _setup(db_session, settings)
    # Created directly (not the `management_user` fixture, which would override the current
    # user and turn the admin calls below into 403s).
    management_user = user_repo.create(
        db_session,
        username="yonetim-test",
        password_hash=hash_password("x"),
        display_name="Yönetim",
        role=UserRole.management,
    )
    db_session.commit()
    contracts = _folder(client, "Proje Sözleşmeleri", "hukuk")
    ankara = Project(name="Ankara RES", code="ANK_RES", stage=ProjectStage.operation)
    izmir = Project(name="İzmir RES", code="IZM_RES", stage=ProjectStage.development)
    db_session.add_all([ankara, izmir])
    db_session.flush()
    normal_a = _document(db_session, title="Ankara normal", department="hukuk", text="a")
    normal_i = _document(db_session, title="İzmir normal", department="hukuk", text="b")
    restricted = _document(db_session, title="Gizli", department="hukuk", text="c")
    for doc, project in ((normal_a, ankara), (normal_i, izmir), (restricted, ankara)):
        doc.folder_id = uuid.UUID(contracts["id"])
        doc.project_id = project.id
    restricted.confidentiality = Confidentiality.restricted
    db_session.commit()
    _grant(client, contracts["id"], "finans", "write")  # even write never lifts confidentiality

    with _as(finans_user):
        assert _visible_ids(client) == {
            str(normal_a.id),
            str(normal_i.id),
        }  # both projects, no restricted
        assert client.get(f"/api/documents/{restricted.id}/download").status_code == 403
        counts = {f["name"]: f["document_count"] for f in client.get("/api/folders").json()}
        assert counts["Proje Sözleşmeleri"] == 2  # what this user can see, not 3
    with _as(management_user):
        assert {str(normal_a.id), str(normal_i.id), str(restricted.id)} <= _visible_ids(client)
        assert all(f["access"] == "write" for f in client.get("/api/folders").json())
    visible = {
        u["username"]
        for u in client.get(f"/api/documents/{restricted.id}/visibility").json()["users"]
    }
    assert finans_user.username not in visible and management_user.username in visible


# ---------------------------------------------------------------- E-07


def test_every_effective_change_is_one_audit_event(
    client: TestClient, db_session: Session, settings: Settings, admin_user: User
) -> None:
    _setup(db_session, settings)
    contracts = _folder(client, "Proje Sözleşmeleri", "hukuk")
    ankara = _folder(client, "Ankara RES", "hukuk", parent_id=contracts["id"])
    _grant(client, contracts["id"], "finans", "read")
    _grant(client, contracts["id"], "finans", "read")  # unchanged → no event
    _grant(client, ankara["id"], "finans", "write")  # effective read → write
    _grant(client, ankara["id"], "finans", "none")  # effective write → read (inherited)
    _grant(client, contracts["id"], "finans", "none")  # read → none

    audit = client.get("/api/admin/folders/audit").json()
    assert [set(e) == AUDIT_KEYS for e in audit] == [True] * 4
    assert [(e["folder_name"], e["before"], e["after"]) for e in audit] == [
        ("Proje Sözleşmeleri", "read", "none"),
        ("Ankara RES", "write", "read"),
        ("Ankara RES", "read", "write"),
        ("Proje Sözleşmeleri", "none", "read"),
    ]
    assert {e["actor_name"] for e in audit} == {admin_user.display_name}
    assert {e["department_slug"] for e in audit} == {"finans"}
    # Granting the owner itself is refused.
    response = client.put(
        f"/api/admin/folders/{contracts['id']}/grants",
        json={"grants": [{"department_slug": "hukuk", "access": "read"}]},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------- E-08 / E-10 / E-11


def test_admin_endpoints_require_admin_and_user_view_is_scoped(
    client: TestClient, db_session: Session, settings: Settings, admin_user: User
) -> None:
    _hukuk, _finans, finans_user = _setup(db_session, settings)
    contracts = _folder(client, "Proje Sözleşmeleri", "hukuk")
    _grant(client, contracts["id"], "finans", "read")
    with _as(finans_user):
        assert client.get("/api/admin/folders").status_code == 403
        assert (
            client.post(
                "/api/admin/folders", json={"name": "x", "owner_department_slug": "finans"}
            ).status_code
            == 403
        )
        assert (
            client.put(
                f"/api/admin/folders/{contracts['id']}/grants", json={"grants": []}
            ).status_code
            == 403
        )
        assert client.get("/api/admin/folders/audit").status_code == 403
        mine = client.get("/api/folders").json()
        assert {(f["name"], f["access"]) for f in mine} == {
            ("Proje Finans", "write"),
            ("Proje Sözleşmeleri", "read"),
        }
        assert all(set(f) == USER_FOLDER_KEYS for f in mine)
    admin_folders = client.get("/api/admin/folders").json()
    assert all(set(f) == ADMIN_FOLDER_KEYS for f in admin_folders)
    assert all(set(g) == GRANT_KEYS for f in admin_folders for g in f["grants"])


def test_tree_rules_owner_match_duplicate_name_move_and_delete(
    client: TestClient, db_session: Session, settings: Settings, admin_user: User
) -> None:
    _setup(db_session, settings)
    contracts = _folder(client, "Proje Sözleşmeleri", "hukuk")
    # Child with a different owner → 422; same name under the same parent → 409.
    bad_owner = client.post(
        "/api/admin/folders",
        json={"name": "Alt", "parent_id": contracts["id"], "owner_department_slug": "finans"},
    )
    assert bad_owner.status_code == 422
    assert (
        client.post(
            "/api/admin/folders",
            json={"name": "Proje Sözleşmeleri", "owner_department_slug": "hukuk"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/admin/folders", json={"name": "x", "owner_department_slug": "yok"}
        ).status_code
        == 404
    )
    ankara = _folder(client, "Ankara RES", "hukuk", parent_id=contracts["id"])
    # Rename; moving a folder under its own descendant → 422.
    assert (
        client.patch(
            f"/api/admin/folders/{ankara['id']}", json={"name": "Ankara RES Sözleşmeleri"}
        ).json()["name"]
        == "Ankara RES Sözleşmeleri"
    )
    assert (
        client.patch(
            f"/api/admin/folders/{contracts['id']}", json={"parent_id": ankara["id"]}
        ).status_code
        == 422
    )
    # Delete: non-empty (has child) → 409; empty leaf → 204; then parent → 204.
    assert client.delete(f"/api/admin/folders/{contracts['id']}").status_code == 409
    doc = _document(db_session, title="d", department="hukuk", text="x")
    doc.folder_id = uuid.UUID(ankara["id"])
    db_session.commit()
    assert client.delete(f"/api/admin/folders/{ankara['id']}").status_code == 409  # has a document
    doc.folder_id = None
    db_session.commit()
    assert client.delete(f"/api/admin/folders/{ankara['id']}").status_code == 204
    assert client.delete(f"/api/admin/folders/{contracts['id']}").status_code == 204
    assert client.delete(f"/api/admin/folders/{uuid.uuid4()}").status_code == 404
