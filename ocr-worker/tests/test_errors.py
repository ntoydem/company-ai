"""Pure classification tests (no DB, no ocrmypdf binary) for worker/errors.py."""

from __future__ import annotations

import pymupdf
from ocrmypdf.exceptions import ExitCode

from worker import errors
from worker.ocr import OcrError


def test_ocrmypdf_exit_code_8_is_encrypted() -> None:
    assert ExitCode.encrypted_pdf == 8  # pinned: the mapping relies on this value
    assert errors.classify(OcrError(8, "EncryptedPdfError")) == errors.ENCRYPTED


def test_other_ocrmypdf_exit_codes_stay_unknown() -> None:
    # exit code 2 also covers DPI / non-embedded font / signature problems — not "corrupt".
    for code in (1, 2, 3, 4, 5, 6, 7, 9, 10, 15):
        assert errors.classify(OcrError(code, "x")) == errors.UNKNOWN


def test_pymupdf_open_failures_are_corrupt() -> None:
    assert errors.classify(pymupdf.FileDataError("cannot open")) == errors.CORRUPT
    assert errors.classify(pymupdf.EmptyFileError("empty")) == errors.CORRUPT
    assert errors.classify(pymupdf.mupdf.FzErrorFormat("premature end of data")) == errors.CORRUPT
    # A decoder/library error is not a proven format violation.
    assert errors.classify(pymupdf.mupdf.FzErrorLibrary("jpeg error")) == errors.UNKNOWN


def test_explicit_failure_keeps_its_code_and_everything_else_is_unknown() -> None:
    assert errors.classify(errors.IngestionError(errors.NO_TEXT)) == errors.NO_TEXT
    assert errors.classify(RuntimeError("boom")) == errors.UNKNOWN
    assert errors.classify(OSError("disk")) == errors.UNKNOWN


def test_only_unknown_is_retryable() -> None:
    assert errors.is_retryable(errors.UNKNOWN)
    for code in (errors.NO_TEXT, errors.ENCRYPTED, errors.CORRUPT):
        assert not errors.is_retryable(code)
