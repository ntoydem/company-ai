"""Per-page text extraction from an OCR'd PDF (PyMuPDF)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pymupdf


def extract_pages(pdf_path: Path) -> Iterator[tuple[int, str]]:
    """Yield (page_number, text) pairs, page_number starting at 1."""
    doc = pymupdf.open(pdf_path)
    try:
        for index in range(doc.page_count):
            yield index + 1, doc[index].get_text()
    finally:
        doc.close()
