"""Tansu Not 7 §2 — the "Son yüklenen belgeler" card endpoint (`GET /api/documents/recent`)
and the failure-code → Turkish `reason` mapping on `/status` and the detail response
(T7-1, T7-2 backend halves). Unflagged: same gate as `/api/documents`."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentReviewStatus, IngestionStatus
from app.models.ingestion_job import IngestionJob, IngestionJobStatus
from app.models.user import User
from app.services import ingestion_errors
from tests.department_fixtures import add_user_to_department, make_department

RAW_CODES = ("no_text", "encrypted", "corrupt", "unknown", "Traceback", "exit code")


def _doc(
    session: Session,
    *,
    title: str = "Belge",
    department: str | None = "finans",
    ingestion_status: IngestionStatus = IngestionStatus.ready,
    review_status: DocumentReviewStatus = DocumentReviewStatus.approved,
    ingestion_error: str | None = None,
    days_ago: int = 0,
    job_status: IngestionJobStatus | None = None,
    uploaded_by: User | None = None,
) -> Document:
    document = Document(
        title=title,
        document_type="dt",
        counterparty="c",
        document_date=date(2026, 1, 1),
        storage_path=f"{uuid.uuid4()}/original.pdf",
        department=department,
        ingestion_status=ingestion_status,
        review_status=review_status,
        ingestion_error=ingestion_error,
        created_at=datetime.now(UTC) - timedelta(days=days_ago),
        uploaded_by_id=uploaded_by.id if uploaded_by else None,
    )
    session.add(document)
    session.flush()
    if job_status is not None:
        session.add(IngestionJob(document_id=document.id, status=job_status))
    session.commit()
    return document


def _state_by_title(client: TestClient, **params: object) -> dict[str, dict[str, object]]:
    response = client.get("/api/documents/recent", params=params)
    assert response.status_code == 200, response.text
    return {item["title"]: item for item in response.json()}


# --- reason mapping -------------------------------------------------------------------


def test_reason_for_maps_known_codes_and_falls_back_to_the_generic_line() -> None:
    assert ingestion_errors.reason_for(None) is None
    assert "Daha net bir tarama" in str(ingestion_errors.reason_for("no_text"))
    assert "parola" in str(ingestion_errors.reason_for("encrypted"))
    assert "bozuk" in str(ingestion_errors.reason_for("corrupt"))
    assert ingestion_errors.reason_for("unknown") == ingestion_errors.GENERIC_REASON
    # Pre-Not 7 rows stored a sentence; the raw stored text is never echoed back.
    assert (
        ingestion_errors.reason_for("Belge işlenirken bir hata oluştu.")
        == ingestion_errors.GENERIC_REASON
    )
    assert (
        ingestion_errors.reason_for("ocrmypdf exited with code 2")
        == ingestion_errors.GENERIC_REASON
    )


def test_unsupported_reason_names_the_real_formats_not_word() -> None:
    reason = ingestion_errors.reason_for("unsupported") or ""
    assert "PDF" in reason and "Excel" in reason and "CSV" in reason
    assert "Word" not in reason


# --- /status and detail (T7-2 backend half) -------------------------------------------


def test_status_returns_turkish_reason_and_never_the_raw_code(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    document = _doc(
        db_session, ingestion_status=IngestionStatus.failed, ingestion_error="encrypted"
    )

    body = client.get(f"/api/documents/{document.id}/status").json()

    assert body["ingestion_status"] == "failed"
    assert body["reason"] == ingestion_errors.REASONS["encrypted"]
    assert body["ingestion_error"] == body["reason"]  # deprecated alias, same Turkish line
    assert not any(code in json.dumps(body) for code in RAW_CODES)


def test_detail_shows_raw_code_to_admin_only(
    client: TestClient, db_session: Session, employee_user: User
) -> None:
    department = make_department(db_session, slug="finans")
    add_user_to_department(db_session, employee_user, department)
    document = _doc(db_session, ingestion_status=IngestionStatus.failed, ingestion_error="no_text")

    body = client.get(f"/api/documents/{document.id}").json()

    assert body["ingestion_reason"] == ingestion_errors.REASONS["no_text"]
    assert body["ingestion_error"] is None


def test_detail_raw_code_visible_to_admin(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    document = _doc(db_session, ingestion_status=IngestionStatus.failed, ingestion_error="no_text")

    body = client.get(f"/api/documents/{document.id}").json()

    assert body["ingestion_error"] == "no_text"
    assert body["ingestion_reason"] == ingestion_errors.REASONS["no_text"]


# --- /recent: card states (T7-1 backend half) -----------------------------------------


def test_recent_card_states_follow_ingestion_job_and_review(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    _doc(
        db_session,
        title="Kuyrukta 1",
        ingestion_status=IngestionStatus.uploaded,
        job_status=IngestionJobStatus.queued,
    )
    _doc(
        db_session,
        title="Kuyrukta 2",
        ingestion_status=IngestionStatus.uploaded,
        job_status=IngestionJobStatus.queued,
    )
    _doc(
        db_session,
        title="Çalışıyor",
        ingestion_status=IngestionStatus.uploaded,
        job_status=IngestionJobStatus.running,
    )
    _doc(
        db_session,
        title="OCR",
        ingestion_status=IngestionStatus.ocr,
        job_status=IngestionJobStatus.running,
    )
    _doc(
        db_session,
        title="Meta bekliyor",
        review_status=DocumentReviewStatus.pending_metadata,
        uploaded_by=admin_user,
    )
    _doc(db_session, title="Müdür bekliyor", review_status=DocumentReviewStatus.pending_review)
    _doc(db_session, title="Geri gönderildi", review_status=DocumentReviewStatus.changes_requested)
    _doc(db_session, title="Hazır")
    _doc(
        db_session,
        title="Okunamadı",
        ingestion_status=IngestionStatus.failed,
        ingestion_error="corrupt",
        job_status=IngestionJobStatus.failed,
    )

    items = _state_by_title(client, limit=20)

    assert items["Kuyrukta 1"]["card_state"] == "queued"
    assert items["Kuyrukta 1"]["queue_position"] == 1
    assert items["Kuyrukta 2"]["queue_position"] == 2
    assert items["Çalışıyor"]["card_state"] == "processing"
    assert items["Çalışıyor"]["queue_position"] is None
    assert items["OCR"]["card_state"] == "processing"
    assert items["Meta bekliyor"]["card_state"] == "pending_approval"
    assert items["Meta bekliyor"]["approver"] == "uploader"
    assert items["Meta bekliyor"]["uploaded_by_id"] == str(admin_user.id)
    assert items["Müdür bekliyor"]["approver"] == "department_manager"
    assert items["Geri gönderildi"]["approver"] == "uploader"
    assert items["Hazır"]["card_state"] == "ready"
    assert items["Hazır"]["approver"] is None and items["Hazır"]["reason"] is None
    assert items["Okunamadı"]["card_state"] == "failed"
    assert items["Okunamadı"]["reason"] == ingestion_errors.REASONS["corrupt"]
    assert not any(code in json.dumps(list(items.values())) for code in RAW_CODES)


def test_recent_window_keeps_unresolved_rows_and_puts_failed_first(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    _doc(db_session, title="Eski hazır", days_ago=30)
    _doc(
        db_session,
        title="Eski okunamadı",
        ingestion_status=IngestionStatus.failed,
        ingestion_error="unknown",
        days_ago=30,
    )
    _doc(
        db_session,
        title="Eski kuyrukta",
        ingestion_status=IngestionStatus.uploaded,
        job_status=IngestionJobStatus.queued,
        days_ago=30,
    )
    _doc(db_session, title="Dün hazır", days_ago=1)
    _doc(db_session, title="Bugün hazır")

    response = client.get("/api/documents/recent")
    titles = [item["title"] for item in response.json()]

    assert "Eski hazır" not in titles
    assert titles[0] == "Eski okunamadı"  # failed first (Naci SORU 3)
    assert titles[1:] == ["Bugün hazır", "Dün hazır", "Eski kuyrukta"]


def test_recent_limit_defaults_to_five_and_caps_at_twenty(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    for i in range(7):
        _doc(db_session, title=f"B{i}")

    assert len(client.get("/api/documents/recent").json()) == 5
    assert len(client.get("/api/documents/recent", params={"limit": 7}).json()) == 7
    assert client.get("/api/documents/recent", params={"limit": 21}).status_code == 422
    assert client.get("/api/documents/recent", params={"limit": 0}).status_code == 422


def test_recent_empty_when_nothing_uploaded(client: TestClient, admin_user: User) -> None:
    assert client.get("/api/documents/recent").json() == []


# --- /recent: the gate (G3) ------------------------------------------------------------


def test_recent_shows_only_what_the_document_list_shows(
    client: TestClient, db_session: Session, employee_user: User
) -> None:
    """An energy employee never sees finance's processing or failed documents — not even
    when asking for `department=finans` explicitly (same gate as `/api/documents`)."""
    enerji = make_department(db_session, slug="enerji")
    make_department(db_session, slug="finans")
    add_user_to_department(db_session, employee_user, enerji)
    _doc(
        db_session,
        title="Enerji işleniyor",
        department="enerji",
        ingestion_status=IngestionStatus.ocr,
        job_status=IngestionJobStatus.running,
    )
    _doc(
        db_session,
        title="Finans işleniyor",
        department="finans",
        ingestion_status=IngestionStatus.ocr,
        job_status=IngestionJobStatus.running,
    )
    _doc(
        db_session,
        title="Finans okunamadı",
        department="finans",
        ingestion_status=IngestionStatus.failed,
        ingestion_error="corrupt",
    )
    _doc(db_session, title="Departmansız", department=None, ingestion_status=IngestionStatus.ocr)

    listed = {d["title"] for d in client.get("/api/documents").json()}
    recent = set(_state_by_title(client, limit=20))
    recent_finans = set(_state_by_title(client, department="finans"))
    recent_enerji = set(_state_by_title(client, department="enerji"))

    assert recent == {"Enerji işleniyor"}
    assert recent <= listed
    assert recent_finans == set()
    assert recent_enerji == {"Enerji işleniyor"}
    assert "Finans" not in json.dumps(client.get("/api/documents/recent?limit=20").json())


def test_recent_includes_own_pending_upload_like_the_list_does(
    client: TestClient, db_session: Session, employee_user: User
) -> None:
    department = make_department(db_session, slug="finans")
    add_user_to_department(db_session, employee_user, department)
    _doc(
        db_session,
        title="Benim taslağım",
        review_status=DocumentReviewStatus.pending_metadata,
        ingestion_status=IngestionStatus.uploaded,
        job_status=IngestionJobStatus.queued,
        uploaded_by=employee_user,
    )
    _doc(
        db_session, title="Başkasının taslağı", review_status=DocumentReviewStatus.pending_metadata
    )

    items = _state_by_title(client)

    assert set(items) == {"Benim taslağım"}
    assert items["Benim taslağım"]["card_state"] == "queued"
