"""Failure classification (Tansu Not 7, 05.10.2026): the worker stores a closed *code* in
`documents.ingestion_error` / `ingestion_jobs.error`, never a sentence and never the raw
exception (that stays in the structured log). The backend maps the code to the plain
Turkish line the user sees (`app/services/ingestion_errors.py`).

A code is assigned only when the cause is certain:

- `encrypted` — ocrmypdf exit code 8 (`ocrmypdf.exceptions.ExitCode.encrypted_pdf`,
  verified against the installed ocrmypdf 17.12.1, not a guess).
- `corrupt`   — PyMuPDF cannot open the file at all (`pymupdf.FileDataError` /
  `pymupdf.EmptyFileError`, checked before OCR for PDFs) or reports a format violation
  while converting an image (`pymupdf.mupdf.FzErrorFormat`, PNG/JPG → PDF).
- `no_text`   — OCR finished and every page came back blank (PDF/image only; the Excel
  family never reaches extraction, by design).
- `unknown`   — everything else, including ocrmypdf's exit code 2 (`input_file`), which
  also covers DPI/font/signature problems and is therefore *not* "corrupt".

`encrypted`/`corrupt`/`no_text` are deterministic: retrying cannot change the outcome, so
the job fails on the first attempt. `unknown` keeps the three attempts (ADR-006).
"""

from __future__ import annotations

import pymupdf
from ocrmypdf.exceptions import ExitCode

from worker.ocr import OcrError

NO_TEXT = "no_text"
ENCRYPTED = "encrypted"
CORRUPT = "corrupt"
UNKNOWN = "unknown"

NON_RETRYABLE: frozenset[str] = frozenset({NO_TEXT, ENCRYPTED, CORRUPT})


class IngestionError(Exception):
    """Raised by the pipeline when it has already established the cause."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


def classify(exc: BaseException) -> str:
    if isinstance(exc, IngestionError):
        return exc.code
    if isinstance(exc, OcrError) and exc.returncode == ExitCode.encrypted_pdf:
        return ENCRYPTED
    if isinstance(exc, pymupdf.FileDataError | pymupdf.EmptyFileError):
        return CORRUPT
    if isinstance(exc, pymupdf.mupdf.FzErrorFormat):
        # MuPDF's "the bytes violate the file format" (e.g. "premature end of data in png
        # image") — certain. Its sibling FzErrorLibrary (decoder errors) is not, → unknown.
        return CORRUPT
    return UNKNOWN


def is_retryable(code: str) -> bool:
    return code not in NON_RETRYABLE
