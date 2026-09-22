"""Job orchestration: lock → OCR → extract → chunk → ready, with retry/failure handling
(ADR-006). One job (and therefore one document) processed per call to `process_one_job`.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import Engine, select, update

from worker import image_to_pdf, ocr, storage
from worker.chunking import chunk_page_text
from worker.config import Config
from worker.db import Tables
from worker.extract import extract_pages

log = logging.getLogger(__name__)

FAILURE_MESSAGE = "Belge işlenirken bir hata oluştu."
MAX_ATTEMPTS = 3


@dataclass(frozen=True)
class LockedJob:
    id: uuid.UUID
    document_id: uuid.UUID
    attempts: int


def requeue_stale_jobs(engine: Engine, tables: Tables, stale_minutes: int) -> int:
    """Crash-recovery safety net (this phase's own addition, not specified by ADR-006):
    a `running` job whose `locked_at` is older than `stale_minutes` is assumed to belong to
    a worker that died mid-job, and is reset to `queued` so it gets picked up again."""
    cutoff = datetime.now(UTC) - timedelta(minutes=stale_minutes)
    with engine.begin() as conn:
        result = conn.execute(
            update(tables.ingestion_jobs)
            .where(tables.ingestion_jobs.c.status == "running")
            .where(tables.ingestion_jobs.c.locked_at < cutoff)
            .values(status="queued")
        )
        return result.rowcount


def lock_next_job(engine: Engine, tables: Tables) -> LockedJob | None:
    with engine.begin() as conn:
        row = conn.execute(
            select(tables.ingestion_jobs.c.id, tables.ingestion_jobs.c.document_id)
            .where(tables.ingestion_jobs.c.status == "queued")
            .order_by(tables.ingestion_jobs.c.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        ).first()
        if row is None:
            return None
        conn.execute(
            update(tables.ingestion_jobs)
            .where(tables.ingestion_jobs.c.id == row.id)
            .values(
                status="running",
                locked_at=datetime.now(UTC),
                attempts=tables.ingestion_jobs.c.attempts + 1,
            )
        )
        attempts = conn.execute(
            select(tables.ingestion_jobs.c.attempts).where(tables.ingestion_jobs.c.id == row.id)
        ).scalar_one()
        return LockedJob(id=row.id, document_id=row.document_id, attempts=attempts)


def _process(engine: Engine, tables: Tables, config: Config, job: LockedJob) -> None:
    # `documents.storage_path` is relative and informational; the file is located directly
    # by globbing the document's directory (its extension varies: pdf/png/jpg).
    original_path = storage.original_file(config.documents_dir, job.document_id)
    extension = original_path.suffix.lstrip(".").lower()
    converted_input: Path | None = None
    if extension in ("png", "jpg", "jpeg"):
        converted_input = original_path.with_name("_ocr_input.pdf")
        image_to_pdf.convert(original_path, converted_input)
        ocr_input = converted_input
    else:
        ocr_input = original_path

    ocr_output = storage.ocr_pdf_path(config.documents_dir, job.document_id)
    try:
        ocr.run_ocr(ocr_input, ocr_output)
    finally:
        if converted_input is not None:
            converted_input.unlink(missing_ok=True)

    with engine.begin() as conn:
        conn.execute(
            update(tables.documents)
            .where(tables.documents.c.id == job.document_id)
            .values(ingestion_status="ocr")
        )

    page_texts: list[tuple[int, str]] = list(extract_pages(ocr_output))
    text_sidecar = storage.text_sidecar_path(config.documents_dir, job.document_id)
    text_sidecar.write_text("\n\f\n".join(text for _, text in page_texts), encoding="utf-8")

    with engine.begin() as conn:
        for page_number, text in page_texts:
            conn.execute(
                tables.document_pages.insert().values(
                    id=uuid.uuid4(),
                    document_id=job.document_id,
                    page_number=page_number,
                    text=text,
                )
            )

        chunk_index = 0
        for page_number, text in page_texts:
            for chunk_text in chunk_page_text(text):
                conn.execute(
                    tables.document_chunks.insert().values(
                        id=uuid.uuid4(),
                        document_id=job.document_id,
                        chunk_index=chunk_index,
                        page_number=page_number,
                        text=chunk_text,
                    )
                )
                chunk_index += 1

        conn.execute(
            update(tables.documents)
            .where(tables.documents.c.id == job.document_id)
            .values(ingestion_status="ready", page_count=len(page_texts))
        )
        conn.execute(
            update(tables.ingestion_jobs)
            .where(tables.ingestion_jobs.c.id == job.id)
            .values(status="done")
        )


def _handle_failure(engine: Engine, tables: Tables, job: LockedJob, exc: Exception) -> None:
    log.error(
        "ingestion job failed",
        extra={"document_id": str(job.document_id), "attempts": job.attempts, "error": repr(exc)},
    )
    with engine.begin() as conn:
        if job.attempts >= MAX_ATTEMPTS:
            conn.execute(
                update(tables.ingestion_jobs)
                .where(tables.ingestion_jobs.c.id == job.id)
                .values(status="failed", error=FAILURE_MESSAGE)
            )
            conn.execute(
                update(tables.documents)
                .where(tables.documents.c.id == job.document_id)
                .values(ingestion_status="failed", ingestion_error=FAILURE_MESSAGE)
            )
        else:
            conn.execute(
                update(tables.ingestion_jobs)
                .where(tables.ingestion_jobs.c.id == job.id)
                .values(status="queued", error=FAILURE_MESSAGE)
            )


def process_one_job(engine: Engine, tables: Tables, config: Config) -> bool:
    """Lock and fully process one queued job. Returns False if the queue was empty."""
    job = lock_next_job(engine, tables)
    if job is None:
        return False
    try:
        _process(engine, tables, config, job)
    except Exception as exc:  # noqa: BLE001 - deliberately broad: any failure must retry/fail the job
        _handle_failure(engine, tables, job, exc)
    return True
