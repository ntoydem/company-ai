"""Idempotent demo documents from `seed_data/documents/manifest.json` (Phase 3.1).

Reads only the JSON manifest `generate_documents.py` writes — never imports
`seed_data.generator` (ADR-013: the generator is never imported by the backend).
Mirrors `demo_projects_seed.py`'s create-if-missing pattern, keyed by `external_ref`.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.excel.inspect import inspect_file
from app.models.document import Confidentiality
from app.models.document import DocumentStatus as DocStatus
from app.repositories import department_repo, document_repo, folder_repo, project_repo, user_repo
from app.services.document_store import LocalFileSystemStore

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DemoSeedResult:
    external_ref: str
    created: bool


def _root_folder_id(session: Session, department_slug: str | None) -> uuid.UUID | None:
    """B-26: seeded documents land in their department's root folder (same place
    migration 0011 puts pre-existing ones)."""
    if department_slug is None:
        return None
    department = department_repo.get_by_slug(session, department_slug)
    if department is None:
        return None
    root = folder_repo.root_for_department(session, department.id)
    return root.id if root else None


def _project_id(session: Session, code: str | None) -> uuid.UUID | None:
    if code is None:
        return None
    project = project_repo.get_by_code(session, code)
    return project.id if project else None


def _seed_one(
    session: Session,
    settings: Settings,
    manifest_dir: Path,
    entry: dict[str, Any],
    uploaded_by_id: uuid.UUID | None,
) -> DemoSeedResult:
    external_ref = entry["external_ref"]
    existing = document_repo.get_by_external_ref(session, external_ref)
    if existing is not None:
        log.info("demo document exists, unchanged", extra={"external_ref": external_ref})
        return DemoSeedResult(external_ref=external_ref, created=False)

    document_id = uuid.uuid4()
    store = LocalFileSystemStore(settings.documents_dir)
    is_workbook = entry.get("source_type") == "xlsx"
    original_name = "original.xlsx" if is_workbook else "original.pdf"
    with (manifest_dir / entry["file"]).open("rb") as stream:
        stored = store.store(document_id, original_name, stream)
    relative_path = str(stored.original_path.relative_to(settings.documents_dir))

    if is_workbook:
        document_repo.create_ready(
            session,
            document_id=document_id,
            title=entry["title"],
            document_type=entry["document_type"],
            document_date=date.fromisoformat(entry["document_date"]),
            counterparty=entry["counterparty"],
            status=DocStatus(entry["status"]),
            tags=entry["tags"],
            storage_path=relative_path,
            uploaded_by_id=uploaded_by_id,
            page_count=len(inspect_file(stored.original_path).sheets),
            file_name=entry["file"],
            version=entry["version_number"],
            department=entry["department"],
            subdepartment=entry["subdepartment"],
            project_id=_project_id(session, entry["project_code"]),
            confidentiality=Confidentiality(entry["confidentiality"]),
            external_ref=external_ref,
            folder_id=_root_folder_id(session, entry["department"]),
        )
        session.commit()
        log.info("demo workbook created", extra={"external_ref": external_ref})
        return DemoSeedResult(external_ref=external_ref, created=True)

    document_repo.create_with_job(
        session,
        document_id=document_id,
        title=entry["title"],
        document_type=entry["document_type"],
        document_date=date.fromisoformat(entry["document_date"]),
        counterparty=entry["counterparty"],
        status=DocStatus(entry["status"]),
        tags=entry["tags"],
        storage_path=relative_path,
        uploaded_by_id=uploaded_by_id,
        effective_date=date.fromisoformat(entry["effective_date"])
        if entry["effective_date"]
        else None,
        version=entry["version_number"],
        department=entry["department"],
        subdepartment=entry["subdepartment"],
        project_id=_project_id(session, entry["project_code"]),
        confidentiality=Confidentiality(entry["confidentiality"]),
        external_ref=external_ref,
        folder_id=_root_folder_id(session, entry["department"]),
    )
    session.commit()
    log.info("demo document created", extra={"external_ref": external_ref})
    return DemoSeedResult(external_ref=external_ref, created=True)


def _relink_chain(session: Session, manifest_dir: Path, entries: list[dict[str, Any]]) -> None:
    """Second pass: `supersedes`/`superseded_by`/`related_document_ids` (docs/plans/
    PHASE_3_1_PLAN.md §4.3). Re-run every time — unlike the document rows themselves,
    the chain is derived from the ledger's *generated* subset and is expected to change
    as later phases add more chain links (e.g. Phase 5.1's V01/V02)."""
    del manifest_dir
    by_ref = {
        e["external_ref"]: document_repo.get_by_external_ref(session, e["external_ref"])
        for e in entries
    }
    changed = False
    for entry in entries:
        document = by_ref[entry["external_ref"]]
        if document is None:
            continue
        predecessor = by_ref.get(entry["supersedes_ref"]) if entry["supersedes_ref"] else None
        if predecessor is not None and document.supersedes_document_id != predecessor.id:
            document.supersedes_document_id = predecessor.id
            predecessor.superseded_by_document_id = document.id
            changed = True
        related_documents = [by_ref.get(ref) for ref in entry["related_refs"]]
        related_ids = [related.id for related in related_documents if related is not None]
        if sorted(map(str, document.related_document_ids)) != sorted(map(str, related_ids)):
            document.related_document_ids = related_ids
            changed = True
    if changed:
        session.commit()


def ensure_demo_documents(
    session: Session, settings: Settings, manifest_path: Path
) -> list[DemoSeedResult]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    admin = user_repo.get_by_username(session, settings.admin_username)
    uploaded_by_id = admin.id if admin else None

    entries = list(manifest["documents"])
    # Phase 4.2 workbooks live in seed_data/excel/manifest.json (committed); seeded through
    # the same idempotent external_ref path, no OCR job, not part of the version chain pass.
    results = [
        _seed_one(session, settings, manifest_path.parent, entry, uploaded_by_id)
        for entry in entries
    ]
    _relink_chain(session, manifest_path.parent, entries)
    excel_manifest = manifest_path.parent.parent / "excel" / "manifest.json"
    if excel_manifest.exists():
        for entry in json.loads(excel_manifest.read_text(encoding="utf-8"))["workbooks"]:
            results.append(
                _seed_one(session, settings, excel_manifest.parent, entry, uploaded_by_id)
            )
    return results
