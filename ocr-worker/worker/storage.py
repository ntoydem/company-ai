"""Path helpers for `$APP_DATA_DIR/documents/<uuid>/{original.<ext>, ocr.pdf, text.txt}`
(ADR-005's `LocalFileSystemStore` layout, mirrored here independently — ocr-worker does
not import `backend/app`)."""

from __future__ import annotations

import uuid
from pathlib import Path


def document_dir(documents_dir: Path, document_id: uuid.UUID) -> Path:
    return documents_dir / str(document_id)


def original_file(documents_dir: Path, document_id: uuid.UUID) -> Path:
    matches = sorted(document_dir(documents_dir, document_id).glob("original.*"))
    if not matches:
        raise FileNotFoundError(f"no original file for document {document_id}")
    return matches[0]


def ocr_pdf_path(documents_dir: Path, document_id: uuid.UUID) -> Path:
    return document_dir(documents_dir, document_id) / "ocr.pdf"


def text_sidecar_path(documents_dir: Path, document_id: uuid.UUID) -> Path:
    return document_dir(documents_dir, document_id) / "text.txt"
