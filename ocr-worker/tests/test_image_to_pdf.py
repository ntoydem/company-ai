from pathlib import Path

import pymupdf

from worker.image_to_pdf import convert


def _make_blank_png(path: Path) -> None:
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 200, 100))
    pix.clear_with(255)  # solid white, no text
    pix.save(path)


def test_image_converts_to_single_page_pdf_with_no_text_layer(tmp_path: Path) -> None:
    png_path = tmp_path / "scan.png"
    _make_blank_png(png_path)
    pdf_path = tmp_path / "converted.pdf"

    convert(png_path, pdf_path)

    assert pdf_path.exists()
    doc = pymupdf.open(pdf_path)
    try:
        assert doc.page_count == 1
        assert doc[0].get_text().strip() == ""
    finally:
        doc.close()
