"""File storage for uploaded documents (ADR-005). Metadata's single source of truth is
Postgres; this interface only ever moves bytes."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import BinaryIO, Literal, Protocol

from pydantic import BaseModel


class StoredFile(BaseModel):
    document_id: uuid.UUID
    original_path: Path
    extension: str


class DocumentStore(Protocol):
    def store(self, document_id: uuid.UUID, filename: str, stream: BinaryIO) -> StoredFile: ...

    def get_file(self, document_id: uuid.UUID, kind: Literal["original", "ocr"]) -> Path: ...

    def get_text(self, document_id: uuid.UUID) -> str: ...


class LocalFileSystemStore:
    """`$APP_DATA_DIR/documents/<uuid>/{original.<ext>, ocr.pdf, text.txt}`.

    `get_text()` reads a sidecar `text.txt` that ocr-worker writes after extraction —
    keeps this interface filesystem-only rather than taking a DB `Session`.
    """

    def __init__(self, documents_dir: Path) -> None:
        self._documents_dir = documents_dir

    def _document_dir(self, document_id: uuid.UUID) -> Path:
        return self._documents_dir / str(document_id)

    def store(self, document_id: uuid.UUID, filename: str, stream: BinaryIO) -> StoredFile:
        # `filename` is caller-controlled (e.g. "original.pdf" from a validated MIME check,
        # never the client's raw filename); .name strips any path components defensively.
        safe_name = Path(filename).name
        document_dir = self._document_dir(document_id)
        document_dir.mkdir(parents=True, exist_ok=True)
        original_path = document_dir / safe_name
        with original_path.open("wb") as out:
            shutil.copyfileobj(stream, out)
        return StoredFile(
            document_id=document_id,
            original_path=original_path,
            extension=original_path.suffix.lstrip("."),
        )

    def get_file(self, document_id: uuid.UUID, kind: Literal["original", "ocr"]) -> Path:
        document_dir = self._document_dir(document_id)
        if kind == "ocr":
            return document_dir / "ocr.pdf"
        matches = sorted(document_dir.glob("original.*"))
        if not matches:
            raise FileNotFoundError(f"no original file for document {document_id}")
        return matches[0]

    def get_text(self, document_id: uuid.UUID) -> str:
        return (self._document_dir(document_id) / "text.txt").read_text(encoding="utf-8")
