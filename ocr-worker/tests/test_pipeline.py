"""End-to-end pipeline tests against the real test database and real ocrmypdf/tesseract
binaries. These generate their own minimal fixture PDFs (do not depend on seed_data/t0/,
a separate, richer fixture set produced elsewhere in this phase)."""

from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path

import pymupdf
import pytest
from sqlalchemy import Engine, func, select

from worker.config import Config
from worker.db import Tables
from worker.pipeline import process_one_job

# Only this module touches the database — opts into the (non-autouse) cleanup fixture.
pytestmark = pytest.mark.usefixtures("_clean_tables")

DSCR_TEXT = "Facility Agreement DEMO DSCR covenant 1.25x minimum"


def _make_digital_pdf(path: Path, page_count: int, text: str) -> None:
    doc = pymupdf.open()
    try:
        for i in range(page_count):
            page = doc.new_page(width=595, height=842)
            page.insert_text((72, 72), f"{text} - page {i + 1}")
        doc.save(path)
    finally:
        doc.close()


def _rasterize_to_scanned_pdf(source_pdf: Path, output_pdf: Path, dpi: int = 150) -> None:
    """Build a no-text-layer PDF from a digital PDF's rasterized pages, so ocrmypdf
    actually has to OCR it (mirrors the shape of a real scanned document)."""
    src = pymupdf.open(source_pdf)
    out = pymupdf.open()
    try:
        for page in src:
            pix = page.get_pixmap(dpi=dpi)
            new_page = out.new_page(width=pix.width, height=pix.height)
            new_page.insert_image(new_page.rect, pixmap=pix)
        out.save(output_pdf)
    finally:
        out.close()
        src.close()


def _insert_document_with_job(
    engine: Engine, tables: Tables, *, document_id: uuid.UUID, title: str, storage_path: str
) -> None:
    with engine.begin() as conn:
        conn.execute(
            tables.documents.insert().values(
                id=document_id,
                title=title,
                document_type="test",
                counterparty="Test A.Ş.",
                document_date=date(2026, 1, 1),
                storage_path=storage_path,
            )
        )
        conn.execute(
            tables.ingestion_jobs.insert().values(
                id=uuid.uuid4(), document_id=document_id, status="queued"
            )
        )


def test_digital_pdf_becomes_ready_with_matching_page_count(
    engine: Engine, tables: Tables, config: Config
) -> None:
    document_id = uuid.uuid4()
    doc_dir = config.documents_dir / str(document_id)
    doc_dir.mkdir(parents=True)
    _make_digital_pdf(doc_dir / "original.pdf", page_count=3, text=DSCR_TEXT)
    _insert_document_with_job(
        engine,
        tables,
        document_id=document_id,
        title="Facility Agreement",
        storage_path=f"{document_id}/original.pdf",
    )

    assert process_one_job(engine, tables, config) is True

    with engine.begin() as conn:
        row = conn.execute(
            select(tables.documents.c.ingestion_status, tables.documents.c.page_count).where(
                tables.documents.c.id == document_id
            )
        ).one()
        page_rows = conn.execute(
            select(func.count())
            .select_from(tables.document_pages)
            .where(tables.document_pages.c.document_id == document_id)
        ).scalar_one()

    assert row.ingestion_status == "ready"
    assert row.page_count == 3
    assert page_rows == 3


def test_scanned_pdf_ocr_produces_readable_text(
    engine: Engine, tables: Tables, config: Config
) -> None:
    document_id = uuid.uuid4()
    doc_dir = config.documents_dir / str(document_id)
    doc_dir.mkdir(parents=True)
    digital_source = doc_dir / "_digital_source.pdf"
    _make_digital_pdf(digital_source, page_count=2, text=DSCR_TEXT)
    _rasterize_to_scanned_pdf(digital_source, doc_dir / "original.pdf")
    digital_source.unlink()

    _insert_document_with_job(
        engine,
        tables,
        document_id=document_id,
        title="Facility Agreement (scanned)",
        storage_path=f"{document_id}/original.pdf",
    )

    assert process_one_job(engine, tables, config) is True

    with engine.begin() as conn:
        status = conn.execute(
            select(tables.documents.c.ingestion_status).where(tables.documents.c.id == document_id)
        ).scalar_one()
        page_texts = (
            conn.execute(
                select(tables.document_pages.c.text).where(
                    tables.document_pages.c.document_id == document_id
                )
            )
            .scalars()
            .all()
        )

    assert status == "ready"
    assert any("DSCR" in text for text in page_texts)
    text_sidecar = doc_dir / "text.txt"
    assert text_sidecar.exists()
    assert "DSCR" in text_sidecar.read_text(encoding="utf-8")


def _make_blank_scanned_pdf(path: Path, page_count: int = 2) -> None:
    """Image-only pages with nothing on them: OCR runs and finds no text."""
    out = pymupdf.open()
    try:
        blank = pymupdf.open()
        blank.new_page(width=595, height=842)
        pix = blank[0].get_pixmap(dpi=100)
        blank.close()
        for _ in range(page_count):
            page = out.new_page(width=pix.width, height=pix.height)
            page.insert_image(page.rect, pixmap=pix)
        out.save(path)
    finally:
        out.close()


def _make_encrypted_pdf(path: Path) -> None:
    doc = pymupdf.open()
    try:
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 72), DSCR_TEXT)
        doc.save(path, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="gizli", owner_pw="sahip")
    finally:
        doc.close()


def _read_outcome(
    engine: Engine, tables: Tables, document_id: uuid.UUID
) -> tuple[str, int, str, str]:
    with engine.begin() as conn:
        job_row = conn.execute(
            select(
                tables.ingestion_jobs.c.status,
                tables.ingestion_jobs.c.attempts,
                tables.ingestion_jobs.c.error,
            ).where(tables.ingestion_jobs.c.document_id == document_id)
        ).one()
        doc_row = conn.execute(
            select(tables.documents.c.ingestion_status, tables.documents.c.ingestion_error).where(
                tables.documents.c.id == document_id
            )
        ).one()
    if job_row.status == "failed":  # a requeued job carries the code, the document not yet
        assert doc_row.ingestion_error == job_row.error
    return job_row.status, job_row.attempts, doc_row.ingestion_status, doc_row.ingestion_error


def _prepare(config: Config, document_id: uuid.UUID) -> Path:
    doc_dir = config.documents_dir / str(document_id)
    doc_dir.mkdir(parents=True)
    return doc_dir


def test_corrupt_pdf_fails_at_once_with_code_corrupt(
    engine: Engine, tables: Tables, config: Config
) -> None:
    """PyMuPDF cannot open the bytes at all → certain, no retry (Not 7, SORU 4)."""
    document_id = uuid.uuid4()
    doc_dir = _prepare(config, document_id)
    (doc_dir / "original.pdf").write_bytes(b"%PDF-1.4\ngarbage, not a real pdf")
    _insert_document_with_job(
        engine, tables, document_id=document_id, title="Corrupt", storage_path="x/original.pdf"
    )

    assert process_one_job(engine, tables, config) is True
    assert process_one_job(engine, tables, config) is False  # nothing requeued

    assert _read_outcome(engine, tables, document_id) == ("failed", 1, "failed", "corrupt")


def test_corrupt_image_fails_at_once_with_code_corrupt(
    engine: Engine, tables: Tables, config: Config
) -> None:
    document_id = uuid.uuid4()
    doc_dir = _prepare(config, document_id)
    (doc_dir / "original.png").write_bytes(b"\x89PNG\r\n\x1a\nnot really an image")
    _insert_document_with_job(
        engine,
        tables,
        document_id=document_id,
        title="Corrupt image",
        storage_path="x/original.png",
    )

    assert process_one_job(engine, tables, config) is True

    assert _read_outcome(engine, tables, document_id) == ("failed", 1, "failed", "corrupt")


def test_encrypted_pdf_fails_at_once_with_code_encrypted(
    engine: Engine, tables: Tables, config: Config
) -> None:
    """ocrmypdf refuses encrypted input with exit code 8 (ExitCode.encrypted_pdf)."""
    document_id = uuid.uuid4()
    doc_dir = _prepare(config, document_id)
    _make_encrypted_pdf(doc_dir / "original.pdf")
    _insert_document_with_job(
        engine, tables, document_id=document_id, title="Encrypted", storage_path="x/original.pdf"
    )

    assert process_one_job(engine, tables, config) is True
    assert process_one_job(engine, tables, config) is False

    assert _read_outcome(engine, tables, document_id) == ("failed", 1, "failed", "encrypted")


def test_blank_scanned_pdf_fails_with_code_no_text_instead_of_silent_ready(
    engine: Engine, tables: Tables, config: Config
) -> None:
    """Before Not 7 this became `ready` with zero chunks (the pipeline never checked);
    now the uploader is told to rescan. No page/chunk rows are written."""
    document_id = uuid.uuid4()
    doc_dir = _prepare(config, document_id)
    _make_blank_scanned_pdf(doc_dir / "original.pdf")
    _insert_document_with_job(
        engine, tables, document_id=document_id, title="Blank scan", storage_path="x/original.pdf"
    )

    assert process_one_job(engine, tables, config) is True

    assert _read_outcome(engine, tables, document_id) == ("failed", 1, "failed", "no_text")
    with engine.begin() as conn:
        pages = conn.execute(
            select(func.count())
            .select_from(tables.document_pages)
            .where(tables.document_pages.c.document_id == document_id)
        ).scalar_one()
    assert pages == 0


def test_unknown_failure_is_retried_three_times_then_fails_with_code_unknown(
    engine: Engine, tables: Tables, config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Anything not certainly classified keeps ADR-006's three attempts. The stored value
    is the code, never the exception text."""
    from worker import pipeline

    def _boom(*_: object, **__: object) -> None:
        raise RuntimeError("tesseract crashed: Traceback (most recent call last) ...")

    monkeypatch.setattr(pipeline.ocr, "run_ocr", _boom)
    document_id = uuid.uuid4()
    doc_dir = _prepare(config, document_id)
    _make_digital_pdf(doc_dir / "original.pdf", page_count=1, text=DSCR_TEXT)
    _insert_document_with_job(
        engine, tables, document_id=document_id, title="Flaky", storage_path="x/original.pdf"
    )

    for _ in range(2):
        assert process_one_job(engine, tables, config) is True
        assert _read_outcome(engine, tables, document_id)[0] == "queued"
    assert process_one_job(engine, tables, config) is True

    assert _read_outcome(engine, tables, document_id) == ("failed", 3, "failed", "unknown")
