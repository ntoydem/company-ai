"""Load the Phase 0.2 T0 documents (real PDFs, real page text) into the test database
without ocr-worker: page text via PyMuPDF, one chunk per page (pages are far below the
800-word chunk size, so this equals the worker's output)."""

from __future__ import annotations

import importlib.util
import uuid
from datetime import date
from pathlib import Path

import pymupdf
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus, IngestionStatus
from app.models.document_chunk import DocumentChunk
from app.models.document_page import DocumentPage

T0_DIR = Path(__file__).resolve().parent.parent / "seed_data" / "t0"
FACILITY_PDF = T0_DIR / "facility_agreement.pdf"
AMENDMENT_PDF = T0_DIR / "amendment_01.pdf"


def ensure_t0_pdfs() -> None:
    if FACILITY_PDF.exists() and AMENDMENT_PDF.exists():
        return
    spec = importlib.util.spec_from_file_location("t0_generate", T0_DIR / "generate.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()


def _load_pdf(
    session: Session,
    *,
    pdf: Path,
    title: str,
    document_date: date,
    department: str | None,
    supersedes: Document | None = None,
) -> Document:
    document = Document(
        title=title,
        document_type="facility_agreement",
        counterparty="PQR Bank A.Ş.",
        document_date=document_date,
        effective_date=document_date,
        status=DocumentStatus.executed,
        department=department,
        storage_path=f"{uuid.uuid4()}/original.pdf",
        ingestion_status=IngestionStatus.ready,
        supersedes_document_id=supersedes.id if supersedes else None,
    )
    session.add(document)
    session.flush()
    with pymupdf.open(pdf) as doc:
        document.page_count = doc.page_count
        for index, page in enumerate(doc, start=1):
            text = page.get_text()
            session.add(DocumentPage(document_id=document.id, page_number=index, text=text))
            session.add(
                DocumentChunk(
                    document_id=document.id, chunk_index=index - 1, page_number=index, text=text
                )
            )
    if supersedes is not None:
        supersedes.superseded_by_document_id = document.id
    session.flush()
    return document


def load_t0_documents(
    session: Session, *, department: str | None = "finance"
) -> tuple[Document, Document]:
    """Facility Agreement (EXECUTED, DSCR 1,25x) → Amendment 01 (DSCR 1,20x), chained."""
    ensure_t0_pdfs()
    facility = _load_pdf(
        session,
        pdf=FACILITY_PDF,
        title="Facility Agreement",
        document_date=date(2023, 6, 1),
        department=department,
    )
    amendment = _load_pdf(
        session,
        pdf=AMENDMENT_PDF,
        title="Amendment 01",
        document_date=date(2025, 3, 15),
        department=department,
        supersedes=facility,
    )
    session.commit()
    return facility, amendment
