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


def _parties_extra_fields(entry: dict[str, Any]) -> dict[str, Any]:
    """Ledger `parties` → `extra_fields.parties` (B-28b, Naci SORU 2): the one piece of
    real document metadata the ledger already records; `key_facts` stay eval references."""
    parties = [str(p) for p in (entry.get("parties") or []) if str(p).strip()]
    if not parties:
        return {}
    return {
        "parties": {
            "value": ", ".join(parties),
            "source": "user",
            "confidence": None,
            "added_by_id": None,
            "added_at": "2026-10-02T00:00:00+00:00",
        }
    }


def _seed_one(
    session: Session,
    settings: Settings,
    manifest_dir: Path,
    entry: dict[str, Any],
    uploaded_by_id: uuid.UUID | None,
) -> DemoSeedResult:
    external_ref = entry["external_ref"]
    extra_fields = _parties_extra_fields(entry)
    existing = document_repo.get_by_external_ref(session, external_ref)
    if existing is not None:
        # B-28b: an existing install gets `parties` once, only when nothing is recorded yet;
        # staff/AI edits are never overwritten by the seed.
        if extra_fields and not existing.extra_fields:
            existing.extra_fields = extra_fields
            session.commit()
            log.info("demo document parties added", extra={"external_ref": external_ref})
            return DemoSeedResult(external_ref=external_ref, created=False)
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
            extra_fields=extra_fields,
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
        expiration_date=date.fromisoformat(entry["expiration_date"])
        if entry.get("expiration_date")
        else None,
        version=entry["version_number"],
        department=entry["department"],
        subdepartment=entry["subdepartment"],
        project_id=_project_id(session, entry["project_code"]),
        confidentiality=Confidentiality(entry["confidentiality"]),
        external_ref=external_ref,
        folder_id=_root_folder_id(session, entry["department"]),
        extra_fields=extra_fields,
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


@dataclass(frozen=True)
class DemoRefreshResult:
    external_ref: str
    changed: dict[str, tuple[str | None, str | None]]  # field -> (before, after)
    found: bool = True


_GATE_FIELDS = ("department", "subdepartment", "confidentiality")


def _manifest_entries(manifest_path: Path) -> dict[str, dict[str, Any]]:
    entries = {
        e["external_ref"]: e
        for e in json.loads(manifest_path.read_text(encoding="utf-8"))["documents"]
    }
    excel_manifest = manifest_path.parent.parent / "excel" / "manifest.json"
    if excel_manifest.exists():
        for e in json.loads(excel_manifest.read_text(encoding="utf-8"))["workbooks"]:
            entries[e["external_ref"]] = e
    return entries


def refresh_demo_document_metadata(
    session: Session, manifest_path: Path, external_refs: list[str]
) -> list[DemoRefreshResult]:
    """Re-seed the *gate* metadata (department, subdepartment, confidentiality, project) of
    named, already-seeded demo documents from the manifest — opt-in, per external_ref.

    The create-if-missing seed never touches an existing row, so a ledger decision such as
    Soru 15 (Financial Model `restricted` → `normal`, 09.10.2026) needs this explicit path
    instead of a full reseed or a hand-written SQL update. Titles, tags, parties and staff
    edits are left alone; only ADR-004 inputs are synced. Before/after values are returned
    (and logged) so the change is auditable."""
    entries = _manifest_entries(manifest_path)
    results: list[DemoRefreshResult] = []
    for external_ref in external_refs:
        entry = entries.get(external_ref)
        document = document_repo.get_by_external_ref(session, external_ref)
        if entry is None or document is None:
            log.warning("demo document refresh: unknown ref", extra={"external_ref": external_ref})
            results.append(DemoRefreshResult(external_ref=external_ref, changed={}, found=False))
            continue
        changed: dict[str, tuple[str | None, str | None]] = {}
        for field in _GATE_FIELDS:
            before = getattr(document, field)
            before_value = before.value if isinstance(before, Confidentiality) else before
            after_value = entry[field]
            if before_value != after_value:
                changed[field] = (before_value, after_value)
                setattr(
                    document,
                    field,
                    Confidentiality(after_value) if field == "confidentiality" else after_value,
                )
        project_id = _project_id(session, entry["project_code"])
        if document.project_id != project_id:
            changed["project_id"] = (
                str(document.project_id) if document.project_id else None,
                str(project_id) if project_id else None,
            )
            document.project_id = project_id
        if changed:
            session.commit()
        log.info(
            "demo document metadata refreshed",
            extra={"external_ref": external_ref, "changed": changed},
        )
        results.append(DemoRefreshResult(external_ref=external_ref, changed=changed))
    return results


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
