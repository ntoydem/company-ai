import io
import uuid
from pathlib import Path

from app.services.document_store import LocalFileSystemStore


def test_store_writes_file_and_get_file_finds_it(tmp_path: Path) -> None:
    store = LocalFileSystemStore(tmp_path)
    document_id = uuid.uuid4()

    stored = store.store(document_id, "original.pdf", io.BytesIO(b"%PDF-1.4 fake"))

    assert stored.extension == "pdf"
    assert store.get_file(document_id, "original") == stored.original_path
    assert stored.original_path.read_bytes() == b"%PDF-1.4 fake"


def test_get_text_reads_sidecar_file(tmp_path: Path) -> None:
    store = LocalFileSystemStore(tmp_path)
    document_id = uuid.uuid4()
    document_dir = tmp_path / str(document_id)
    document_dir.mkdir()
    (document_dir / "text.txt").write_text("page one text", encoding="utf-8")

    assert store.get_text(document_id) == "page one text"


def test_get_file_ocr_kind_returns_ocr_pdf_path(tmp_path: Path) -> None:
    store = LocalFileSystemStore(tmp_path)
    document_id = uuid.uuid4()

    assert store.get_file(document_id, "ocr") == tmp_path / str(document_id) / "ocr.pdf"
