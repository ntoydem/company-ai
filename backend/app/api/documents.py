"""Document upload, listing and status (SPEC_02 §1–2, ADR-004/005/006)."""

import io
import logging
import uuid
from datetime import date
from typing import Annotated, BinaryIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.core.db import get_session
from app.models.document import DocumentStatus
from app.models.user import User
from app.repositories import document_repo
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.authorization import AuthorizationScope
from app.schemas.document import DocumentListItem, DocumentStatusResponse, DocumentUploadResponse
from app.services.authorization import allowed_document_ids
from app.services.document_store import LocalFileSystemStore

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
) -> DocumentUploadResponse:
    content = _read_within_limit(file.file, settings.max_upload_size_mb * 1024 * 1024)
    extension = _detect_extension(content)
    if extension is None:
        raise HTTPException(415, UNSUPPORTED_FILE_TYPE_MESSAGE)

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
