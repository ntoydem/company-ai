"""Document upload, listing and status (SPEC_02 §1–2, ADR-004/005/006)."""

import io
import logging
import uuid
import zipfile
from datetime import date
from typing import Annotated, BinaryIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_llm_client, require_admin
from app.core.config import Settings, get_settings
from app.core.db import get_session
from app.excel.inspect import inspect_file
from app.models.document import Confidentiality, Document, DocumentStatus, IngestionStatus
from app.models.document_metadata_suggestion import SuggestionStatus
from app.models.user import User, UserRole
from app.repositories import (
    department_repo,
    document_metadata_suggestion_repo,
    document_repo,
    project_repo,
    user_repo,
)
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.authorization import AuthorizationScope
from app.schemas.document import (
    DocumentDetailResponse,
    DocumentListItem,
    DocumentMetadataEditRequest,
    DocumentStatusResponse,
    DocumentUploadResponse,
    DocumentVisibilityResponse,
    DocumentVisibilityUser,
    MetadataSuggestionApplyRequest,
    MetadataSuggestionResponse,
)
from app.services import metadata_suggestion
from app.services.authorization import SingleDocumentIdsProvider, allowed_document_ids
from app.services.document_store import LocalFileSystemStore
from app.services.llm import LLMClient

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

# pdf/png/jpg (Phase 0.2) go through the OCR pipeline; xlsx/xlsm/csv (Phase 4.2, SPEC_02 §1)
# are the Excel family — stored as-is, `ready` without a job, read by `app/excel/`.
_MAGIC_BYTES: dict[bytes, str] = {
    b"%PDF-": "pdf",
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpg",
}
_ZIP_MAGIC = b"PK\x03\x04"
EXCEL_EXTENSIONS = frozenset({"xlsx", "xlsm", "csv"})
UNSUPPORTED_FILE_TYPE_MESSAGE = "Desteklenmeyen dosya türü."
FILE_TOO_LARGE_MESSAGE = "Dosya çok büyük."
DOCUMENT_NOT_FOUND_MESSAGE = "Belge bulunamadı."
ALREADY_SUPERSEDED_MESSAGE = "Belge zaten başka bir belge tarafından güncellenmiş."
DOCUMENT_ACCESS_DENIED_MESSAGE = "Bu belgeye erişim yetkiniz yok."
UNKNOWN_DEPARTMENT_MESSAGE = "Bilinmeyen departman."
DEPARTMENT_NOT_ALLOWED_MESSAGE = "Bu departmana belge yükleme yetkiniz yok."
UNKNOWN_PROJECT_MESSAGE = "Bilinmeyen proje."
NOT_READY_MESSAGE = "Belge henüz işleniyor, öneri üretilemez."
SUGGESTION_NOT_FOUND_MESSAGE = "Öneri bulunamadı."
FIELD_CANNOT_BE_NULL_MESSAGE = "Bu alan boş bırakılamaz."
# Nullable on `documents` — an explicit `null` in the apply request clears the field.
_CLEARABLE_FIELDS = frozenset({"department", "subdepartment", "project_code"})
# The manual edit endpoint (Phase 5.2) also exposes `effective_date`/`expiration_date`,
# both nullable on `documents` — `title` is not nullable, so it stays out of this set.
_EDIT_CLEARABLE_FIELDS = _CLEARABLE_FIELDS | frozenset({"effective_date", "expiration_date"})


def _resolve_metadata_updates(
    session: Session,
    provided: set[str],
    body: MetadataSuggestionApplyRequest | DocumentMetadataEditRequest,
    *,
    clearable_fields: frozenset[str],
) -> dict[str, object]:
    """Shared by the AI-suggestion apply flow and the manual edit endpoint (Phase 5.2):
    only fields present in `body` are written (SPEC_02 §4), `department`/`project_code`
    resolve to the same validated slug/id lookups either way."""
    updates: dict[str, object] = {}
    for field in provided:
        value = getattr(body, field)
        if value is None and field not in clearable_fields:
            raise HTTPException(422, FIELD_CANNOT_BE_NULL_MESSAGE)
        if field == "department":
            if value is not None and department_repo.get_by_slug(session, value) is None:
                raise HTTPException(422, UNKNOWN_DEPARTMENT_MESSAGE)
            updates["department"] = value
        elif field == "project_code":
            if value is None:
                updates["project_id"] = None
            else:
                project = project_repo.get_by_code(session, value)
                if project is None:
                    raise HTTPException(404, UNKNOWN_PROJECT_MESSAGE)
                updates["project_id"] = project.id
        else:
            updates[field] = value
    return updates


def _detect_extension(content: bytes, filename: str | None = None) -> str | None:
    """Content-sniffed, never the declared extension alone: a zip is only an Excel file
    when it carries `xl/workbook.xml`, and it is `xlsm` (macros flagged, never run) when
    it also carries `xl/vbaProject.bin`. CSV has no signature — accepted only when the
    declared name ends in .csv, the bytes decode as UTF-8 and a delimiter is found."""
    for signature, extension in _MAGIC_BYTES.items():
        if content.startswith(signature):
            return extension
    if content.startswith(_ZIP_MAGIC):
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                names = set(archive.namelist())
        except zipfile.BadZipFile:
            return None
        if "xl/workbook.xml" not in names:
            return None
        return "xlsm" if "xl/vbaProject.bin" in names else "xlsx"
    if filename and filename.lower().endswith(".csv"):
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            return None
        return "csv" if any(d in text for d in (",", ";", "\t", "|")) else None
    return None


def _safe_file_name(filename: str | None, extension: str) -> str:
    """Basename only, no path separators, extension normalised to the sniffed one."""
    base = (filename or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
    stem = base.rsplit(".", 1)[0] if "." in base else base
    return f"{stem or 'workbook'}.{extension}"[:255]


def _read_within_limit(stream: BinaryIO, max_bytes: int) -> bytes:
    data = stream.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(413, FILE_TOO_LARGE_MESSAGE)
    return data


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
def upload_document(
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    current_user: Annotated[User, Depends(get_current_user)],
    file: Annotated[UploadFile, File()],
    title: Annotated[str, Form()],
    document_type: Annotated[str, Form()],
    document_date: Annotated[date, Form()],
    counterparty: Annotated[str, Form()],
    status: Annotated[DocumentStatus, Form()] = DocumentStatus.draft,
    effective_date: Annotated[date | None, Form()] = None,
    version: Annotated[int, Form(ge=1)] = 1,
    supersedes_document_id: Annotated[uuid.UUID | None, Form()] = None,
    department: Annotated[str | None, Form()] = None,
    subdepartment: Annotated[str | None, Form()] = None,
    project_id: Annotated[uuid.UUID | None, Form()] = None,
    confidentiality: Annotated[Confidentiality, Form()] = Confidentiality.normal,
) -> DocumentUploadResponse:
    content = _read_within_limit(file.file, settings.max_upload_size_mb * 1024 * 1024)
    extension = _detect_extension(content, file.filename)
    if extension is None:
        raise HTTPException(415, UNSUPPORTED_FILE_TYPE_MESSAGE)

    # SPEC_02 §1 form fields (Phase 3.2): all optional at upload — the AI suggestion +
    # apply flow can fill them in afterwards. `department` is validated against the known
    # slug list here (PHASES.md Phase 1.2 note); `subdepartment` stays free text, it is a
    # display/filter field, never an authorization unit (docs/plans/PHASE_1_2_PLAN.md T7).
    if department is not None and department_repo.get_by_slug(session, department) is None:
        raise HTTPException(422, UNKNOWN_DEPARTMENT_MESSAGE)
    # Security patch (30.09.2026, docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md Tansu #6):
    # a known slug alone isn't enough — an employee could name a department they don't
    # belong to and plant a document into its retrieval (ADR-004's read-side gate never
    # covered this write-side path). `management`/`admin` already see every department on
    # the read side, so they stay exempt; `department=None` is untouched (fail-safe today).
    if (
        department is not None
        and current_user.role not in (UserRole.management, UserRole.admin)
        and department not in current_user.department_slugs
    ):
        raise HTTPException(403, DEPARTMENT_NOT_ALLOWED_MESSAGE)
    if project_id is not None and project_repo.get(session, project_id) is None:
        raise HTTPException(404, UNKNOWN_PROJECT_MESSAGE)

    # Version chain (ADR-012): the predecessor must be visible to the user (ADR-004) and
    # not already superseded (chains are linear, DOMAIN_MODEL §6). Checked before the
    # file is stored so a rejected upload leaves nothing on disk.
    predecessor = None
    if supersedes_document_id is not None:
        allowed = allowed_document_ids(
            current_user, AuthorizationScope(), SqlDocumentIdsProvider(session)
        )
        if supersedes_document_id not in allowed:
            raise HTTPException(404, DOCUMENT_NOT_FOUND_MESSAGE)
        predecessor = document_repo.get(session, supersedes_document_id)
        if predecessor is None:
            raise HTTPException(404, DOCUMENT_NOT_FOUND_MESSAGE)
        if predecessor.superseded_by_document_id is not None:
            raise HTTPException(409, ALREADY_SUPERSEDED_MESSAGE)

    document_id = uuid.uuid4()
    store = LocalFileSystemStore(settings.documents_dir)
    stored = store.store(document_id, f"original.{extension}", io.BytesIO(content))
    relative_path = str(stored.original_path.relative_to(settings.documents_dir))

    if extension in EXCEL_EXTENSIONS:
        # Excel family: no OCR, no chunks (SPEC_04 §1 — workbooks are not RAG documents);
        # sheets are read at query time. Macros are flagged from the zip, never loaded.
        info = inspect_file(stored.original_path)
        document = document_repo.create_ready(
            session,
            document_id=document_id,
            title=title,
            document_type=document_type,
            document_date=document_date,
            counterparty=counterparty,
            status=status,
            tags=[],
            storage_path=relative_path,
            uploaded_by_id=current_user.id,
            page_count=len(info.sheets),
            has_macros=info.has_macros,
            file_name=_safe_file_name(file.filename, extension),
            effective_date=effective_date,
            version=version,
            department=department,
            subdepartment=subdepartment,
            project_id=project_id,
            confidentiality=confidentiality,
        )
        document.supersedes_document_id = supersedes_document_id
    else:
        document = document_repo.create_with_job(
            session,
            document_id=document_id,
            title=title,
            document_type=document_type,
            document_date=document_date,
            counterparty=counterparty,
            status=status,
            tags=[],
            storage_path=relative_path,
            uploaded_by_id=current_user.id,
            effective_date=effective_date,
            version=version,
            supersedes_document_id=supersedes_document_id,
            department=department,
            subdepartment=subdepartment,
            project_id=project_id,
            confidentiality=confidentiality,
        )
    if predecessor is not None:
        document_repo.mark_superseded(session, older=predecessor, newer=document)
    session.commit()
    log.info(
        "document uploaded",
        extra={"document_id": str(document.id), "extension": extension, "size": len(content)},
    )
    return DocumentUploadResponse.model_validate(document)


@router.get("", response_model=list[DocumentListItem])
def list_documents(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    department: str | None = None,
    project_id: uuid.UUID | None = None,
) -> list[DocumentListItem]:
    scope = AuthorizationScope(department=department, project_id=project_id)
    allowed = allowed_document_ids(current_user, scope, SqlDocumentIdsProvider(session))
    return [DocumentListItem.model_validate(d) for d in document_repo.list_by_ids(session, allowed)]


@router.get("/{document_id}/download")
def download_document(
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    current_user: Annotated[User, Depends(get_current_user)],
    document_id: uuid.UUID,
) -> FileResponse:
    """403 rather than the 404 the other endpoints below use for an unauthorized id — the
    acceptance criterion text asks for 403 here specifically; a deliberate, documented
    exception to the "hide existence" pattern (docs/plans/PHASE_1_2_PLAN.md T6)."""
    allowed = allowed_document_ids(
        current_user, AuthorizationScope(), SqlDocumentIdsProvider(session)
    )
    if document_id not in allowed:
        raise HTTPException(403, DOCUMENT_ACCESS_DENIED_MESSAGE)
    document = document_repo.get(session, document_id)
    if document is None:
        raise HTTPException(404, DOCUMENT_NOT_FOUND_MESSAGE)
    try:
        path = LocalFileSystemStore(settings.documents_dir).get_file(document.id, kind="original")
    except FileNotFoundError:
        raise HTTPException(404, DOCUMENT_NOT_FOUND_MESSAGE) from None
    return FileResponse(path, filename=path.name)


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    document_id: uuid.UUID,
) -> DocumentStatusResponse:
    allowed = allowed_document_ids(
        current_user, AuthorizationScope(), SqlDocumentIdsProvider(session)
    )
    if document_id not in allowed:
        raise HTTPException(404, DOCUMENT_NOT_FOUND_MESSAGE)
    document = document_repo.get(session, document_id)
    if document is None:
        raise HTTPException(404, DOCUMENT_NOT_FOUND_MESSAGE)
    return DocumentStatusResponse.model_validate(document)


def _get_authorized_document(session: Session, user: User, document_id: uuid.UUID) -> Document:
    allowed = allowed_document_ids(user, AuthorizationScope(), SqlDocumentIdsProvider(session))
    if document_id not in allowed:
        raise HTTPException(404, DOCUMENT_NOT_FOUND_MESSAGE)
    document = document_repo.get(session, document_id)
    if document is None:
        raise HTTPException(404, DOCUMENT_NOT_FOUND_MESSAGE)
    return document


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    document_id: uuid.UUID,
) -> DocumentDetailResponse:
    """Full metadata for one visible document (Phase 3.3, SORU 1). Unauthorized ids get
    the same 404 as `/status` (existence hidden; `/download` alone answers 403)."""
    document = _get_authorized_document(session, current_user, document_id)
    return DocumentDetailResponse.model_validate(document)


@router.post("/{document_id}/suggest-metadata", response_model=MetadataSuggestionResponse)
def trigger_metadata_suggestion(
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    current_user: Annotated[User, Depends(require_admin)],
    llm: Annotated[LLMClient, Depends(get_llm_client)],
    document_id: uuid.UUID,
) -> MetadataSuggestionResponse:
    """Admin-only (SORU 2, docs/plans/PHASE_3_2_PLAN.md). Idempotent while a suggestion is
    `pending`/`applied` — returns the existing row rather than reclassifying; a `failed` or
    `rejected` one is regenerated. The same background scan (`app/main.py` lifespan) calls
    `metadata_suggestion.suggest_metadata` directly for documents with no suggestion yet."""
    document = _get_authorized_document(session, current_user, document_id)
    if document.ingestion_status != IngestionStatus.ready:
        raise HTTPException(409, NOT_READY_MESSAGE)
    existing = document_metadata_suggestion_repo.get_by_document_id(session, document_id)
    if existing is not None and existing.status in (
        SuggestionStatus.pending,
        SuggestionStatus.applied,
    ):
        return MetadataSuggestionResponse.model_validate(existing)
    suggestion = metadata_suggestion.suggest_metadata(session, document, llm, settings)
    return MetadataSuggestionResponse.model_validate(suggestion)


@router.get("/{document_id}/metadata-suggestion", response_model=MetadataSuggestionResponse)
def get_metadata_suggestion(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    document_id: uuid.UUID,
) -> MetadataSuggestionResponse:
    _get_authorized_document(session, current_user, document_id)
    suggestion = document_metadata_suggestion_repo.get_by_document_id(session, document_id)
    if suggestion is None:
        raise HTTPException(404, SUGGESTION_NOT_FOUND_MESSAGE)
    return MetadataSuggestionResponse.model_validate(suggestion)


@router.post("/{document_id}/metadata-suggestion/apply", response_model=DocumentListItem)
def apply_metadata_suggestion(
    body: MetadataSuggestionApplyRequest,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_admin)],
    document_id: uuid.UUID,
) -> DocumentListItem:
    """Admin-only (SORU 2). Only fields present in `body` are written — SPEC_02 §4's
    "kritik alan sessiz overwrite yok" applies to every field uniformly, not a subset:
    nothing changes unless its value is explicitly given here."""
    document = _get_authorized_document(session, current_user, document_id)
    suggestion = document_metadata_suggestion_repo.get_by_document_id(session, document_id)
    if suggestion is None:
        raise HTTPException(404, SUGGESTION_NOT_FOUND_MESSAGE)

    updates = _resolve_metadata_updates(
        session, body.model_fields_set, body, clearable_fields=_CLEARABLE_FIELDS
    )
    document_repo.apply_partial_update(session, document, updates)
    document_metadata_suggestion_repo.mark_applied(
        session, suggestion, applied_by_id=current_user.id
    )
    session.commit()
    return DocumentListItem.model_validate(document)


@router.post("/{document_id}/metadata-suggestion/reject", response_model=MetadataSuggestionResponse)
def reject_metadata_suggestion(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_admin)],
    document_id: uuid.UUID,
) -> MetadataSuggestionResponse:
    """Admin-only (SORU 2). Leaves the document untouched; a later `suggest-metadata` call
    regenerates the (now `rejected`) row."""
    _get_authorized_document(session, current_user, document_id)
    suggestion = document_metadata_suggestion_repo.get_by_document_id(session, document_id)
    if suggestion is None:
        raise HTTPException(404, SUGGESTION_NOT_FOUND_MESSAGE)
    document_metadata_suggestion_repo.mark_rejected(session, suggestion)
    session.commit()
    return MetadataSuggestionResponse.model_validate(suggestion)


@router.patch("/{document_id}", response_model=DocumentDetailResponse)
def edit_document_metadata(
    document_id: uuid.UUID,
    body: DocumentMetadataEditRequest,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_admin)],
) -> DocumentDetailResponse:
    """Admin-only manual metadata edit (Phase 5.2, SORU 1), independent of the
    AI-suggestion flow above — works whether or not a suggestion was ever generated.
    Version-chain fields are not exposed here (ADR-012, see schema docstring)."""
    document = _get_authorized_document(session, current_user, document_id)
    updates = _resolve_metadata_updates(
        session, body.model_fields_set, body, clearable_fields=_EDIT_CLEARABLE_FIELDS
    )
    document_repo.apply_partial_update(session, document, updates)
    session.commit()
    return DocumentDetailResponse.model_validate(document)


@router.get("/{document_id}/visibility", response_model=DocumentVisibilityResponse)
def get_document_visibility(
    document_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_admin)],
) -> DocumentVisibilityResponse:
    """Admin-only "bu belgeyi kim görebilir" lookup (Phase 5.2) — reuses
    `allowed_document_ids` in reverse via `SingleDocumentIdsProvider` rather than a second
    permission engine (ADR-004)."""
    document = _get_authorized_document(session, current_user, document_id)
    provider = SingleDocumentIdsProvider(document)
    visible_users = [
        user
        for user in user_repo.list_all(session)
        if document.id in allowed_document_ids(user, AuthorizationScope(), provider)
    ]
    return DocumentVisibilityResponse(
        document_id=document.id,
        department=document.department,
        confidentiality=document.confidentiality,
        users=[DocumentVisibilityUser.model_validate(user) for user in visible_users],
    )
