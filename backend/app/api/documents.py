"""Document upload, listing and status (SPEC_02 §1–2, ADR-004/005/006)."""

import io
import logging
import uuid
from datetime import date
from typing import Annotated, BinaryIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_llm_client, require_admin
from app.core.config import Settings, get_settings
from app.core.db import get_session
from app.models.document import Confidentiality, Document, DocumentStatus, IngestionStatus
from app.models.document_metadata_suggestion import SuggestionStatus
from app.models.user import User
from app.repositories import (
    department_repo,
    document_metadata_suggestion_repo,
    document_repo,
    project_repo,
)
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.authorization import AuthorizationScope
from app.schemas.document import (
    DocumentListItem,
    DocumentStatusResponse,
    DocumentUploadResponse,
    MetadataSuggestionApplyRequest,
    MetadataSuggestionResponse,
)
from app.services import metadata_suggestion
from app.services.authorization import allowed_document_ids
from app.services.document_store import LocalFileSystemStore
from app.services.llm import LLMClient

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Only these three are in scope for Phase 0.2 (SPEC_02 §1 also lists xlsx/xlsm/csv,
# which land with the Excel engine in Phase 4.2).
_MAGIC_BYTES: dict[bytes, str] = {
    b"%PDF-": "pdf",
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpg",
}
UNSUPPORTED_FILE_TYPE_MESSAGE = "Desteklenmeyen dosya türü."
FILE_TOO_LARGE_MESSAGE = "Dosya çok büyük."
DOCUMENT_NOT_FOUND_MESSAGE = "Belge bulunamadı."
ALREADY_SUPERSEDED_MESSAGE = "Belge zaten başka bir belge tarafından güncellenmiş."
DOCUMENT_ACCESS_DENIED_MESSAGE = "Bu belgeye erişim yetkiniz yok."
UNKNOWN_DEPARTMENT_MESSAGE = "Bilinmeyen departman."
UNKNOWN_PROJECT_MESSAGE = "Bilinmeyen proje."
NOT_READY_MESSAGE = "Belge henüz işleniyor, öneri üretilemez."
SUGGESTION_NOT_FOUND_MESSAGE = "Öneri bulunamadı."
FIELD_CANNOT_BE_NULL_MESSAGE = "Bu alan boş bırakılamaz."
# Nullable on `documents` — an explicit `null` in the apply request clears the field.
_CLEARABLE_FIELDS = frozenset({"department", "subdepartment", "project_code"})


def _detect_extension(header: bytes) -> str | None:
    for signature, extension in _MAGIC_BYTES.items():
        if header.startswith(signature):
            return extension
    return None


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
    extension = _detect_extension(content)
    if extension is None:
        raise HTTPException(415, UNSUPPORTED_FILE_TYPE_MESSAGE)

    # SPEC_02 §1 form fields (Phase 3.2): all optional at upload — the AI suggestion +
    # apply flow can fill them in afterwards. `department` is validated against the known
    # slug list here (PHASES.md Phase 1.2 note); `subdepartment` stays free text, it is a
    # display/filter field, never an authorization unit (docs/plans/PHASE_1_2_PLAN.md T7).
    if department is not None and department_repo.get_by_slug(session, department) is None:
        raise HTTPException(422, UNKNOWN_DEPARTMENT_MESSAGE)
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

    provided = body.model_fields_set
    updates: dict[str, object] = {}
    for field in provided:
        value = getattr(body, field)
        if value is None and field not in _CLEARABLE_FIELDS:
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
