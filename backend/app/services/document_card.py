"""Server-side state of the "Son yüklenen belgeler" card (Tansu Not 7, §2). Pure functions:
no session, no LLM. The authorization gate is the caller's (`GET /api/documents/recent`
uses exactly the `/api/documents` call).

    uploaded + job queued   → queued           ("Kuyrukta · Sırada N.")
    uploaded + job running  → processing       ("İşleniyor…")
    ocr                     → processing
    ready + not approved    → pending_approval ("Onay bekliyor" + whose move)
    ready + approved        → ready            ("Hazır ✓ — Balbal kullanabilir")
    failed                  → failed           (mapped Turkish `reason`)
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping

from app.models.document import Document, DocumentReviewStatus, IngestionStatus
from app.models.ingestion_job import IngestionJob, IngestionJobStatus
from app.schemas.document import Approver, CardState, RecentDocumentItem
from app.services.ingestion_errors import reason_for

# Still on the card after the 7-day window: the user has something to do or wait for.
UNRESOLVED_STATUSES: frozenset[IngestionStatus] = frozenset(
    {IngestionStatus.uploaded, IngestionStatus.ocr, IngestionStatus.failed}
)
RECENT_WINDOW_DAYS = 7
DEFAULT_LIMIT = 5
MAX_LIMIT = 20


def card_state(document: Document, job: IngestionJob | None) -> CardState:
    status = document.ingestion_status
    if status == IngestionStatus.failed:
        return "failed"
    if status == IngestionStatus.ready:
        if document.review_status == DocumentReviewStatus.approved:
            return "ready"
        return "pending_approval"
    if status == IngestionStatus.ocr:
        return "processing"
    # uploaded: the job row says whether the worker has picked it up yet.
    if job is not None and job.status == IngestionJobStatus.running:
        return "processing"
    return "queued"


def approver_for(document: Document) -> Approver | None:
    """Whose move a pending document waits for (B-28 two-stage review, ADR-024)."""
    if document.review_status == DocumentReviewStatus.pending_review:
        return "department_manager"
    if document.review_status in (
        DocumentReviewStatus.pending_metadata,
        DocumentReviewStatus.changes_requested,
    ):
        return "uploader"
    return None


def build_recent_items(
    documents: Iterable[Document],
    jobs_by_document: Mapping[uuid.UUID, IngestionJob],
    queued_job_ids_in_order: list[uuid.UUID],
) -> list[RecentDocumentItem]:
    position_by_job = {job_id: i + 1 for i, job_id in enumerate(queued_job_ids_in_order)}
    items: list[RecentDocumentItem] = []
    for document in documents:
        job = jobs_by_document.get(document.id)
        state = card_state(document, job)
        items.append(
            RecentDocumentItem(
                document_id=document.id,
                title=document.title,
                document_type=document.document_type,
                file_kind=document.file_kind,
                created_at=document.created_at,
                uploaded_by_id=document.uploaded_by_id,
                ingestion_status=document.ingestion_status,
                review_status=document.review_status,
                card_state=state,
                queue_position=(
                    position_by_job.get(job.id) if state == "queued" and job is not None else None
                ),
                approver=approver_for(document) if state == "pending_approval" else None,
                reason=reason_for(document.ingestion_error) if state == "failed" else None,
            )
        )
    return items
