"""B-28 — two-stage document approval (ADR-024, NOT §5.2). Acceptance criteria O-01..O-12 of
`docs/plans/B28_ONAY_AKISI_PLAN.md`. No real LLM: `fake_llm` answers `/api/ask`, the AI
suggestion rows are seeded directly."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import Settings
from app.main import app
from app.models.audit_log import AuditLog
from app.models.department import Department
from app.models.document import Document, DocumentReviewStatus, DocumentStatus, IngestionStatus
from app.models.document_chunk import DocumentChunk
from app.models.document_metadata_suggestion import SuggestionStatus
from app.models.document_review_event import DocumentReviewEvent
from app.models.user import User, UserRole
from app.repositories import document_metadata_suggestion_repo, user_repo
from app.services import document_review
from app.services.answer_prompt import NO_ANSWER_TEXT
from app.services.security import hash_password
from tests.department_fixtures import (
    add_user_to_department,
    make_department,
    make_department_manager,
)
from tests.fakes import FakeLLMClient
from tests.test_documents import _upload
from tests.test_excel_api import EXCEL_DIR, XLSX_TYPE


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


def _user(session: Session, username: str, role: UserRole, *departments: Department) -> User:
    user = user_repo.create(
        session,
        username=username,
        password_hash=hash_password("x"),
        display_name=username,
        role=role,
    )
    session.commit()  # users without a membership would otherwise never be committed
    for department in departments:
        add_user_to_department(session, user, department)
    return user


class Cast:
    """finans with its manager, two employees, a hukuk manager, management and admin."""

    def __init__(self, session: Session, settings: Settings) -> None:
        self.finans = make_department(session, slug="finans", name="Proje Finans")
        self.hukuk = make_department(session, slug="hukuk", name="Hukuk")
        self.finans_manager = make_department_manager(session, self.finans, "finans-mudur")
        self.hukuk_manager = make_department_manager(session, self.hukuk, "hukuk-mudur")
        self.uploader = _user(session, "finans-yukleyen", UserRole.employee, self.finans)
        self.colleague = _user(session, "finans-mesai", UserRole.employee, self.finans)
        self.management = _user(session, "genel-mudur", UserRole.management)
        self.admin = user_repo.get_by_username(session, settings.admin_username)
        assert self.admin is not None


@pytest.fixture
def cast(db_session: Session, settings: Settings, admin_user: User) -> Cast:
    del admin_user
    return Cast(db_session, settings)


def _ids(client: TestClient, **params: str) -> set[str]:
    response = client.get("/api/documents", params=params)
    assert response.status_code == 200, response.text
    return {row["id"] for row in response.json()}


def _make_ready_with_chunk(session: Session, document_id: str, text: str) -> None:
    document = session.get(Document, uuid.UUID(document_id))
    assert document is not None
    document.ingestion_status = IngestionStatus.ready
    session.add(DocumentChunk(document_id=document.id, chunk_index=0, page_number=1, text=text))
    session.commit()


def _seed_suggestion(session: Session, document_id: str, fields: dict[str, object]) -> None:
    document_metadata_suggestion_repo.upsert(
        session,
        document_id=uuid.UUID(document_id),
        model="fake-model",
        status=SuggestionStatus.pending,
        fields=fields,
    )
    session.commit()


def _status(session: Session, document_id: str) -> DocumentReviewStatus:
    session.expire_all()
    document = session.get(Document, uuid.UUID(document_id))
    assert document is not None
    return document.review_status


def _events(session: Session, document_id: str) -> list[str]:
    stmt = (
        select(DocumentReviewEvent.kind)
        .where(DocumentReviewEvent.document_id == uuid.UUID(document_id))
        .order_by(DocumentReviewEvent.created_at, DocumentReviewEvent.id)
    )
    return [k.value for k in session.scalars(stmt).all()]


def _ask(client: TestClient, question: str) -> dict[str, object]:
    response = client.post("/api/ask", json={"question": question})
    assert response.status_code == 200, response.text
    body: dict[str, object] = response.json()
    return body


# ------------------------------------------------------------------ O-01 / O-02 upload


def test_employee_upload_is_pending_and_hidden_from_everyone_but_the_handlers(
    client: TestClient, db_session: Session, cast: Cast, fake_llm: FakeLLMClient
) -> None:
    with _as(cast.uploader):
        response = _upload(client, department="finans", title="Kredi Tadili")
        assert response.status_code == 201, response.text
        document_id = response.json()["id"]
        # The uploader handles it: list, detail — but it is not knowledge yet.
        assert document_id in _ids(client)
        detail = client.get(f"/api/documents/{document_id}").json()
        assert detail["review_status"] == "pending_metadata"
        _make_ready_with_chunk(db_session, document_id, "Kredi tadili faiz marjı 2,10")
        body = _ask(client, "faiz marjı nedir?")
        assert body["answered"] is False and body["answer"] == NO_ANSWER_TEXT
        assert fake_llm.requests == []  # not even a prompt was built
        search = client.get("/api/search", params={"q": "Kredi Tadili"}).json()
        assert document_id not in {d["id"] for d in search["documents"]}
    with _as(cast.colleague):
        assert document_id not in _ids(client)
        assert client.get(f"/api/documents/{document_id}").status_code == 404
    with _as(cast.management):
        assert document_id not in _ids(client)  # no general privilege (NOT §5.2)
    with _as(cast.finans_manager):
        assert document_id in _ids(client, review_status="pending_metadata")  # the queue
    with _as(cast.hukuk_manager):
        assert document_id not in _ids(client)
    # admin sees every pending document (handling view), still not as knowledge.
    assert document_id in _ids(client)
    assert _events(db_session, document_id) == ["uploaded"]


def test_only_the_target_departments_manager_publishes_at_once(
    client: TestClient, db_session: Session, cast: Cast
) -> None:
    with _as(cast.finans_manager):
        own = _upload(client, department="finans").json()["id"]
    assert _status(db_session, own) == DocumentReviewStatus.approved
    assert _events(db_session, own) == ["uploaded", "auto_approved"]
    with _as(cast.colleague):
        assert own in _ids(client)  # published for the department right away

    with _as(cast.hukuk_manager):  # another department's manager: no shortcut, 403 anyway
        assert _upload(client, department="finans").status_code == 403
    with _as(cast.management):
        by_management = _upload(client, department="finans").json()["id"]
    by_admin = _upload(client, department="finans").json()["id"]
    assert _status(db_session, by_management) == DocumentReviewStatus.pending_metadata
    assert _status(db_session, by_admin) == DocumentReviewStatus.pending_metadata


# ------------------------------------------------------------------ O-07 approver missing


def test_upload_without_a_configured_approver_is_refused_before_anything_is_stored(
    client: TestClient, db_session: Session, settings: Settings, cast: Cast
) -> None:
    make_department(db_session, slug="idari_isler")  # no manager anywhere
    files_before = sum(1 for _ in settings.documents_dir.rglob("*") if _.is_file())
    rows_before = db_session.scalar(select(func.count()).select_from(Document))

    response = _upload(client, department="idari_isler")  # admin, still needs an approver

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "approver_not_configured"
    assert sum(1 for _ in settings.documents_dir.rglob("*") if _.is_file()) == files_before
    assert db_session.scalar(select(func.count()).select_from(Document)) == rows_before
    # A department-less upload has no approver by definition and is not refused (SORU 1a).
    orphan = _upload(client)
    assert orphan.status_code == 201
    assert _status(db_session, orphan.json()["id"]) == DocumentReviewStatus.pending_metadata


# ------------------------------------------------------------------ O-03 / O-04 submit


def test_submit_is_the_uploaders_act_and_enforces_the_confidence_threshold(
    client: TestClient, db_session: Session, cast: Cast
) -> None:
    with _as(cast.uploader):
        document_id = _upload(client, department="finans").json()["id"]
        # Still processing → the suggestion is not there yet.
        early = client.post(f"/api/documents/{document_id}/submit", json={})
        assert early.status_code == 409 and early.json()["detail"]["code"] == "suggestion_pending"
    _make_ready_with_chunk(db_session, document_id, "metin")
    _seed_suggestion(
        db_session,
        document_id,
        {
            "department": {"value": "finans", "confidence": 0.95},
            "counterparty": {"value": "X Bank", "confidence": 0.55},
            "document_type": {"value": "amendment", "confidence": 0.4},
        },
    )
    body = {"department": "finans", "counterparty": "X Bank", "document_type": "facility"}
    with _as(cast.colleague):
        assert client.post(f"/api/documents/{document_id}/submit", json=body).status_code == 404
    with _as(cast.finans_manager):  # can see it, may not submit for someone else
        assert client.post(f"/api/documents/{document_id}/submit", json=body).status_code == 403
    admin_try = client.post(f"/api/documents/{document_id}/submit", json=body)
    assert admin_try.status_code == 403  # admin sees it, may not submit for someone else
    with _as(cast.uploader):
        refused = client.post(f"/api/documents/{document_id}/submit", json=body)
        assert refused.status_code == 422, refused.text
        detail = refused.json()["detail"]
        assert detail["code"] == "low_confidence_not_confirmed"
        assert detail["fields"] == ["counterparty"]  # document_type was *changed* → explicit

        accepted = client.post(
            f"/api/documents/{document_id}/submit",
            json={**body, "confirmed_fields": ["counterparty"]},
        )
        assert accepted.status_code == 200, accepted.text
        assert accepted.json()["review_status"] == "pending_review"
        assert accepted.json()["counterparty"] == "X Bank"
        assert accepted.json()["document_type"] == "facility"
        again = client.post(f"/api/documents/{document_id}/submit", json=body)
        assert again.status_code == 409
        assert again.json()["detail"]["code"] == "review_state_conflict"
    assert _events(db_session, document_id) == [
        "uploaded",
        "field_confirmed",
        "field_edited",
        "submitted",
    ]
    suggestion = document_metadata_suggestion_repo.get_by_document_id(
        db_session, uuid.UUID(document_id)
    )
    assert suggestion is not None and suggestion.status == SuggestionStatus.applied


def test_submit_needs_a_department(client: TestClient, db_session: Session, cast: Cast) -> None:
    with _as(cast.uploader):
        document_id = _upload(client).json()["id"]  # department-less
        _make_ready_with_chunk(db_session, document_id, "metin")
        _seed_suggestion(db_session, document_id, {})
        response = client.post(f"/api/documents/{document_id}/submit", json={})
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "department_required"
        # Naming the department in the submission itself is enough.
        ok = client.post(f"/api/documents/{document_id}/submit", json={"department": "finans"})
        assert ok.status_code == 200 and ok.json()["review_status"] == "pending_review"


# ------------------------------------------------------------------ O-05 / O-06 review


def _submitted_document(client: TestClient, session: Session, cast: Cast, text: str) -> str:
    with _as(cast.uploader):
        document_id = _upload(client, department="finans", title="Tadil").json()["id"]
    _make_ready_with_chunk(session, document_id, text)
    _seed_suggestion(session, document_id, {"department": {"value": "finans", "confidence": 0.9}})
    with _as(cast.uploader):
        response = client.post(
            f"/api/documents/{document_id}/submit", json={"department": "finans"}
        )
        assert response.status_code == 200, response.text
    return document_id


def test_only_the_target_departments_manager_reviews_and_approval_publishes(
    client: TestClient, db_session: Session, cast: Cast, fake_llm: FakeLLMClient
) -> None:
    document_id = _submitted_document(client, db_session, cast, "Tadil ile faiz marjı 2,10 oldu")
    approve = {"decision": "approve"}
    url = f"/api/documents/{document_id}/review"
    with _as(cast.uploader):
        assert client.post(url, json=approve).status_code == 403
    with _as(cast.colleague):
        assert client.post(url, json=approve).status_code == 404  # cannot even see it
    with _as(cast.management):
        assert client.post(url, json=approve).status_code == 404
    with _as(cast.hukuk_manager):
        assert client.post(url, json=approve).status_code == 404
    assert client.post(url, json=approve).status_code == 403  # admin sees it, may not approve
    # Before approval: a colleague asking Balbal gets nothing.
    with _as(cast.colleague):
        before = _ask(client, "faiz marjı kaç oldu?")
        assert before["answered"] is False and fake_llm.requests == []
    with _as(cast.finans_manager):
        response = client.post(url, json=approve)
        assert response.status_code == 200, response.text
        assert response.json()["review_status"] == "approved"
        assert client.post(url, json=approve).status_code == 409  # already decided
    with _as(cast.colleague):
        fake_llm.replies = ["Faiz marjı 2,10 oldu [K1]."]
        after = _ask(client, "faiz marjı kaç oldu?")
        assert after["answered"] is True
        assert after["retrieved_document_ids"] == [document_id]
        assert document_id in _ids(client)
    assert _events(db_session, document_id)[-1] == "approved"


def test_request_changes_needs_a_comment_and_the_uploader_resubmits(
    client: TestClient, db_session: Session, cast: Cast
) -> None:
    document_id = _submitted_document(client, db_session, cast, "metin")
    url = f"/api/documents/{document_id}/review"
    with _as(cast.finans_manager):
        bare = client.post(url, json={"decision": "request_changes"})
        assert bare.status_code == 422 and bare.json()["detail"]["code"] == "comment_required"
        sent_back = client.post(
            url, json={"decision": "request_changes", "comment": "Karşı taraf adı eksik."}
        )
        assert sent_back.status_code == 200
        assert sent_back.json()["review_status"] == "changes_requested"
    with _as(cast.uploader):
        detail = client.get(f"/api/documents/{document_id}").json()
        assert detail["review_comment"] == "Karşı taraf adı eksik."
        assert document_id in _ids(client, review_status="changes_requested")
        again = client.post(
            f"/api/documents/{document_id}/submit", json={"counterparty": "PQR Bank A.Ş."}
        )
        assert again.status_code == 200 and again.json()["review_status"] == "pending_review"
        assert again.json()["review_comment"] is None
    assert _events(db_session, document_id)[-2:] == ["changes_requested", "resubmitted"]


# ------------------------------------------------------------------ O-08 Excel


def test_pending_workbook_stays_out_of_the_excel_catalogue_until_approved(
    client: TestClient, db_session: Session, cast: Cast, fake_llm: FakeLLMClient
) -> None:
    with _as(cast.uploader):
        response = client.post(
            "/api/documents/upload",
            files={
                "file": (
                    "Covenant_Report.xlsx",
                    (EXCEL_DIR / "Covenant_Report.xlsx").read_bytes(),
                    XLSX_TYPE,
                )
            },
            data={
                "title": "Covenant Report",
                "document_type": "Covenant Report",
                "document_date": "2026-08-15",
                "counterparty": "PQR Bank",
                "department": "finans",
            },
        )
        assert response.status_code == 201, response.text
        document_id = response.json()["id"]
        assert client.get(f"/api/excel/{document_id}/inspect").status_code == 200
    with _as(cast.colleague):
        assert client.get(f"/api/excel/{document_id}/inspect").status_code == 404
        body = client.post("/api/excel/ask", json={"question": "DSCR?"}).json()
        assert body["answered"] is False and body["excel_files"] == []
        assert fake_llm.requests == []  # no catalogue → no planning call
    with _as(cast.uploader):  # no AI suggestion for a workbook: typed fields are confirmed
        submitted = client.post(f"/api/documents/{document_id}/submit", json={})
        assert submitted.status_code == 200
        assert submitted.json()["review_status"] == "pending_review"
    with _as(cast.finans_manager):
        approved = client.post(f"/api/documents/{document_id}/review", json={"decision": "approve"})
        assert approved.status_code == 200
    with _as(cast.colleague):
        assert client.get(f"/api/excel/{document_id}/inspect").status_code == 200
        assert document_id in _ids(client)


# ------------------------------------------------------------------ O-09 T9


def test_editing_an_approved_document_reopens_the_review_unless_the_manager_does_it(
    client: TestClient, db_session: Session, cast: Cast
) -> None:
    document = Document(
        title="Onaylı",
        document_type="dt",
        counterparty="c",
        document_date=date(2026, 1, 1),
        department="finans",
        status=DocumentStatus.executed,
        storage_path=f"{uuid.uuid4()}/original.pdf",
    )
    db_session.add(document)
    db_session.commit()
    document_id = str(document.id)
    assert _status(db_session, document_id) == DocumentReviewStatus.approved

    unchanged = client.patch(f"/api/documents/{document_id}", json={"title": "Onaylı"})
    assert unchanged.status_code == 200 and unchanged.json()["review_status"] == "approved"
    edited = client.patch(f"/api/documents/{document_id}", json={"title": "Onaylı v2"})
    assert edited.status_code == 200 and edited.json()["review_status"] == "pending_review"
    assert _events(db_session, document_id) == ["metadata_changed_after_approval"]
    # The approver's own edit keeps the approval (pure rule, no edit endpoint for them yet).
    document.review_status = DocumentReviewStatus.approved
    db_session.commit()
    assert document_review.is_target_manager(cast.finans_manager, "finans")
    assert not document_review.is_target_manager(cast.hukuk_manager, "finans")
    assert not document_review.is_target_manager(cast.admin, "finans")


# ------------------------------------------------------------------ O-10 version chain


def test_a_pending_amendment_does_not_hide_the_current_document(
    client: TestClient, db_session: Session, cast: Cast, fake_llm: FakeLLMClient
) -> None:
    with _as(cast.finans_manager):
        original = _upload(client, department="finans", title="Kredi Sözleşmesi").json()["id"]
    _make_ready_with_chunk(db_session, original, "Kredi sözleşmesi DSCR covenant 1,25x")
    with _as(cast.uploader):
        amendment = _upload(
            client,
            department="finans",
            title="Tadil 01",
            supersedes_document_id=original,
            version="2",
        )
        assert amendment.status_code == 201, amendment.text
    with _as(cast.colleague):
        fake_llm.replies = ["DSCR covenant 1,25x [K1]."]
        body = _ask(client, "DSCR covenant nedir?")
        assert body["retrieved_document_ids"] == [original]
        assert body["answered"] is True
        assert amendment.json()["id"] not in _ids(client)


# ------------------------------------------------------------------ O-11 visibility


def test_visibility_of_a_pending_document_lists_only_its_handlers(
    client: TestClient, db_session: Session, cast: Cast
) -> None:
    with _as(cast.uploader):
        document_id = _upload(client, department="finans").json()["id"]
    response = client.get(f"/api/documents/{document_id}/visibility")
    assert response.status_code == 200
    body = response.json()
    assert body["review_status"] == "pending_metadata"
    assert {u["username"] for u in body["users"]} == {
        cast.uploader.username,
        cast.finans_manager.username,
        cast.admin.username,
    }


# ------------------------------------------------------------------ O-12 ledger


def test_review_events_are_admin_only_and_never_touch_the_audit_log(
    client: TestClient, db_session: Session, cast: Cast
) -> None:
    document_id = _submitted_document(client, db_session, cast, "metin")
    with _as(cast.finans_manager):
        client.post(f"/api/documents/{document_id}/review", json={"decision": "approve"})
    with _as(cast.uploader):
        assert client.get(f"/api/admin/documents/{document_id}/review-events").status_code == 403
    with _as(cast.finans_manager):
        assert client.get(f"/api/admin/documents/{document_id}/review-events").status_code == 403
    events = client.get(f"/api/admin/documents/{document_id}/review-events")
    assert events.status_code == 200
    assert [e["kind"] for e in events.json()] == ["uploaded", "submitted", "approved"]
    assert events.json()[0]["actor_name"] == cast.uploader.display_name
    assert events.json()[-1]["actor_name"] == cast.finans_manager.display_name
    assert db_session.scalar(select(func.count()).select_from(AuditLog)) == 0
    assert client.get(f"/api/admin/documents/{uuid.uuid4()}/review-events").status_code == 404
