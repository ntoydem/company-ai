"""Job orchestration: lock → OCR → extract → chunk → ready, with retry/failure handling
(ADR-006). One job (and therefore one document) processed per call to `process_one_job`.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pymupdf
from sqlalchemy import Engine, select, update

from worker import errors, image_to_pdf, ocr, storage
from worker.chunking import chunk_page_text
from worker.config import Config
from worker.db import Tables
from worker.extract import extract_pages

log = logging.getLogger(__name__)

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
    if extension in ("xlsx", "xlsm", "csv"):
        # Excel family never gets a job (Phase 4.2: the upload marks it ready directly);
        # if one ever appears, finish it without touching ocrmypdf — never a failure.
        with engine.begin() as conn:
            conn.execute(
                update(tables.documents)
                .where(tables.documents.c.id == job.document_id)
                .values(ingestion_status="ready")
            )
            conn.execute(
                update(tables.ingestion_jobs)
                .where(tables.ingestion_jobs.c.id == job.id)
                .values(status="done")
            )
        return
    converted_input: Path | None = None
    if extension in ("png", "jpg", "jpeg"):
        converted_input = original_path.with_name("_ocr_input.pdf")
        # A corrupt image raises pymupdf.FileDataError here → `corrupt` (worker/errors.py).
        image_to_pdf.convert(original_path, converted_input)
        ocr_input = converted_input
    else:
        _assert_openable_pdf(original_path)
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
    if not any(text.strip() for _, text in page_texts):
        # Before Not 7 this silently became `ready` with zero chunks — invisible to search
        # and to the uploader alike. Now it is a failure the user can act on (rescan).
        raise errors.IngestionError(errors.NO_TEXT, f"{len(page_texts)} blank page(s)")
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


def _assert_openable_pdf(path: Path) -> None:
    """`corrupt` must be certain (Naci, Not 7 SORU 4): only "PyMuPDF cannot open it" counts.
    ocrmypdf's own exit code 2 is ambiguous (DPI, fonts, signatures) and stays `unknown`."""
    doc = pymupdf.open(path)  # raises pymupdf.FileDataError / EmptyFileError
    doc.close()


def _handle_failure(engine: Engine, tables: Tables, job: LockedJob, exc: Exception) -> None:
    """Store a closed error *code* (worker/errors.py), never a sentence or the exception.
    Deterministic causes fail at once; `unknown` is retried up to `MAX_ATTEMPTS`."""
    code = errors.classify(exc)
    final = job.attempts >= MAX_ATTEMPTS or not errors.is_retryable(code)
    log.error(
        "ingestion job failed",
        extra={
            "document_id": str(job.document_id),
            "attempts": job.attempts,
            "code": code,
            "final": final,
            "error": repr(exc),
        },
    )
    with engine.begin() as conn:
        if final:
            conn.execute(
                update(tables.ingestion_jobs)
                .where(tables.ingestion_jobs.c.id == job.id)
                .values(status="failed", error=code)
            )
            conn.execute(
                update(tables.documents)
                .where(tables.documents.c.id == job.document_id)
                .values(ingestion_status="failed", ingestion_error=code)
            )
        else:
            conn.execute(
                update(tables.ingestion_jobs)
                .where(tables.ingestion_jobs.c.id == job.id)
                .values(status="queued", error=code)
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
