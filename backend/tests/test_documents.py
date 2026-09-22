import uuid
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.ingestion_job import IngestionJob, IngestionJobStatus
from app.models.user import User

FAKE_PDF = b"%PDF-1.4\n%fake-pdf-for-tests\n1 0 obj\n<< >>\nendobj\ntrailer\n<< >>\n%%EOF"


def _upload(
    client: TestClient,
    *,
    filename: str = "facility_agreement.pdf",
    content: bytes = FAKE_PDF,
    content_type: str = "application/pdf",
    title: str = "Facility Agreement",
    document_type: str = "facility_agreement",
    document_date: str = "2023-06-01",
    counterparty: str = "PQR Bank",
    **extra: str,
):
    return client.post(
        "/api/documents/upload",
        files={"file": (filename, content, content_type)},
        data={
            "title": title,
            "document_type": document_type,
            "document_date": document_date,
            "counterparty": counterparty,
            **extra,
        },
    )


def test_upload_creates_document_and_job_row(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    response = _upload(client)
    assert response.status_code == 201
    body = response.json()
    assert body["ingestion_status"] == "uploaded"
    document_id = uuid.UUID(body["id"])

    document = db_session.get(Document, document_id)
    assert document is not None
    assert document.title == "Facility Agreement"
    assert document.uploaded_by_id == admin_user.id
    # Defaults per PHASES.md Phase 0.2 scope: not accepted from the client yet.
    assert document.department is None
    assert document.project_id is None
    assert document.confidentiality.value == "normal"

    job = db_session.scalar(select(IngestionJob).where(IngestionJob.document_id == document_id))
    assert job is not None
    assert job.status == IngestionJobStatus.queued
    assert job.attempts == 0


def test_upload_missing_required_field_returns_422(client: TestClient, admin_user: User) -> None:
    response = client.post(
        "/api/documents/upload",
        files={"file": ("f.pdf", FAKE_PDF, "application/pdf")},
        data={"document_type": "facility_agreement", "document_date": "2023-06-01"},
    )
    assert response.status_code == 422


def test_upload_exe_rejected_with_415(client: TestClient, admin_user: User) -> None:
    response = _upload(
        client,
        filename="virus.exe",
        content=b"MZ\x90\x00not-a-real-exe",
        content_type="application/octet-stream",
    )
    assert response.status_code == 415


def test_upload_corrupt_but_pdf_shaped_file_is_accepted_at_upload_time(
    client: TestClient, admin_user: User
) -> None:
    """A truncated/malformed PDF still has a valid `%PDF-` header, so upload succeeds —
    the corruption is only caught by ocr-worker's pipeline (kabul kriteri 3a)."""
    response = _upload(client, content=b"%PDF-1.4\nthis is not a real pdf body")
    assert response.status_code == 201


def test_list_documents_returns_uploaded_document(client: TestClient, admin_user: User) -> None:
    upload_response = _upload(client)
    document_id = upload_response.json()["id"]

    response = client.get("/api/documents")
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert document_id in ids


def test_get_document_status_returns_fields(client: TestClient, admin_user: User) -> None:
    document_id = _upload(client).json()["id"]

    response = client.get(f"/api/documents/{document_id}/status")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == document_id
    assert body["ingestion_status"] == "uploaded"
    assert body["ingestion_error"] is None
    assert body["page_count"] is None


def test_get_document_status_404_for_unknown_id(client: TestClient, admin_user: User) -> None:
    response = client.get(f"/api/documents/{uuid.uuid4()}/status")
    assert response.status_code == 404


def test_upload_with_supersedes_links_the_chain(
    client: TestClient, db_session: Session, admin_user: User
) -> None:
    facility = _upload(client, status="executed", effective_date="2023-06-01").json()
    facility_id = uuid.UUID(facility["id"])
    response = _upload(
        client,
        title="Amendment 01",
        document_date="2025-03-15",
        status="executed",
        effective_date="2025-03-15",
        version="1",
        supersedes_document_id=str(facility_id),
    )
    assert response.status_code == 201
    amendment = db_session.get(Document, uuid.UUID(response.json()["id"]))
    facility = db_session.get(Document, facility_id)
    assert amendment is not None and facility is not None
    assert amendment.supersedes_document_id == facility_id
    assert amendment.effective_date == date(2025, 3, 15)
    assert facility.superseded_by_document_id == amendment.id
    assert facility.status.value == "executed"  # unchanged (Phase 0.3 decision)


def test_upload_supersedes_already_superseded_is_409(client: TestClient, admin_user: User) -> None:
    facility_id = _upload(client).json()["id"]
    assert _upload(client, title="Amd 1", supersedes_document_id=facility_id).status_code == 201
    response = _upload(client, title="Amd 1 again", supersedes_document_id=facility_id)
    assert response.status_code == 409
    assert response.json()["detail"] == "Belge zaten başka bir belge tarafından güncellenmiş."


def test_upload_supersedes_unknown_document_is_404(client: TestClient, admin_user: User) -> None:
    response = _upload(client, supersedes_document_id=str(uuid.uuid4()))
    assert response.status_code == 404


def test_upload_version_must_be_positive(client: TestClient, admin_user: User) -> None:
    assert _upload(client, version="0").status_code == 422
