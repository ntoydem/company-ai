"""Load Phase 3.1 ledger-generated documents into the test database (real PDFs, real
page text) without ocr-worker, and resolve ledger values for assertions — replaces the
Adım 0 `t0_fixtures.py` now that the truth ledger produces real demo documents.

Tests intentionally import `seed_data.generator` directly (as `t0_fixtures.py` did for
`seed_data/t0/generate.py`) — ADR-013 forbids `app/` (production code) from importing
the generator, not the test suite reading its output for fixtures.
"""

from __future__ import annotations

import json
import uuid
from datetime import date
from pathlib import Path
from typing import Any

import pymupdf
from sqlalchemy.orm import Session

from app.models.document import Confidentiality, Document, DocumentStatus, IngestionStatus
from app.models.document_chunk import DocumentChunk
from app.models.document_page import DocumentPage
from seed_data.generator import facts as facts_mod
from seed_data.generator.validate_ledger import resolve_path

DOCUMENTS_DIR = Path(__file__).resolve().parent.parent / "seed_data" / "documents"
MANIFEST_PATH = DOCUMENTS_DIR / "manifest.json"

_raws_cache: dict[str, Any] | None = None


def _raws() -> dict[str, Any]:
    global _raws_cache
    if _raws_cache is None:
        _raws_cache = facts_mod.load_raws()
    return _raws_cache


def ensure_generated_documents() -> dict[str, Any]:
    """Renders the 15 documents from the committed prose if `manifest.json` is missing
    (first test run in a fresh checkout) — no LLM call, same as `make seed`."""
    if not MANIFEST_PATH.exists():
        from seed_data.generator.generate_documents import generate

        generate()
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def ledger_value(path: str) -> Any:
    """`path` = "<ankara_res|izmir_res|company|fx_rates>.<dotted.ledger.path>" — the
    same path format as `documents[].key_facts` and `questions.json`'s `ledger:` prefix
    (without the prefix). Lets tests assert against the ledger instead of a literal
    figure (CLAUDE.md: demo numbers only ever come from `seed_data/master/*.yaml`)."""
    ledger_key, _, rest = path.partition(".")
    return resolve_path(_raws()[ledger_key], rest)


def page_of(manifest: dict[str, Any], external_ref: str, heading_or_marker: str) -> int:
    entry = next(e for e in manifest["documents"] if e["external_ref"] == external_ref)
    page: int = entry["page_map"][heading_or_marker]
    return page


def _load_one(session: Session, entry: dict[str, Any]) -> Document:
    document_id = uuid.uuid4()
    pdf_path = DOCUMENTS_DIR / (entry["digital_file"] or entry["file"])
    document = Document(
        id=document_id,
        title=entry["title"],
        document_type=entry["document_type"],
        counterparty=entry["counterparty"],
        document_date=date.fromisoformat(entry["document_date"]),
        effective_date=date.fromisoformat(entry["effective_date"])
        if entry["effective_date"]
        else None,
        status=DocumentStatus(entry["status"]),
        department=entry["department"],
        subdepartment=entry["subdepartment"],
        confidentiality=Confidentiality(entry["confidentiality"]),
        version=entry["version_number"],
        storage_path=f"{document_id}/original.pdf",
        ingestion_status=IngestionStatus.ready,
        external_ref=entry["external_ref"],
    )
    session.add(document)
    session.flush()
    with pymupdf.open(pdf_path) as pdf:
        document.page_count = pdf.page_count
        for index, page in enumerate(pdf, start=1):
            text = page.get_text()
            session.add(DocumentPage(document_id=document.id, page_number=index, text=text))
            session.add(
                DocumentChunk(
                    document_id=document.id, chunk_index=index - 1, page_number=index, text=text
                )
            )
    session.flush()
    return document


def load_ledger_documents(session: Session, refs: list[str]) -> dict[str, Document]:
    """Loads the given `external_ref`s; links `supersedes`/`superseded_by` between
    whichever of them are both present in `refs` (mirrors `demo_documents_seed.py`'s
    nearest-generated-ancestor rule, restricted to this test's own subset)."""
    manifest = ensure_generated_documents()
    by_ref = {e["external_ref"]: e for e in manifest["documents"]}
    loaded: dict[str, Document] = {ref: _load_one(session, by_ref[ref]) for ref in refs}
    for ref in refs:
        supersedes_ref = by_ref[ref]["supersedes_ref"]
        if supersedes_ref in loaded:
            loaded[ref].supersedes_document_id = loaded[supersedes_ref].id
            loaded[supersedes_ref].superseded_by_document_id = loaded[ref].id
    session.commit()
    return loaded
