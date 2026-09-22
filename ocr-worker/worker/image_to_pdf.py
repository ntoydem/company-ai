"""png/jpg → single-page PDF (ADR-006: "png/jpg converted to PDF first").

Uses PyMuPDF only (already a hard dependency for page-text extraction) rather than adding
`img2pdf` — see docs/plans/PHASE_0_2_PLAN.md §2 for the trade-off this accepts.
"""

from __future__ import annotations

from pathlib import Path

import pymupdf


def convert(image_path: Path, output_pdf_path: Path) -> None:
    image_doc = pymupdf.open(image_path)
    try:
        pdf_bytes = image_doc.convert_to_pdf()
    finally:
        image_doc.close()
    pdf_doc = pymupdf.open("pdf", pdf_bytes)
    try:
        pdf_doc.save(output_pdf_path)
    finally:
        pdf_doc.close()
