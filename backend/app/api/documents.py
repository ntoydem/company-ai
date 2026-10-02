"""Document upload, listing and status (SPEC_02 §1–2, ADR-004/005/006)."""

import io
import logging
import re
import uuid
import zipfile
from datetime import UTC, date, datetime
from typing import Annotated, BinaryIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_llm_client, require_admin
from app.core.config import Settings, get_settings
from app.core.db import get_session
from app.excel.inspect import inspect_file
from app.models.document import (
    Confidentiality,
    Document,
    DocumentReviewStatus,
    DocumentStatus,
    FileKind,
    IngestionStatus,
)
from app.models.document_metadata_suggestion import SuggestionStatus
from app.models.document_review_event import ReviewEventKind
from app.models.user import User, UserRole
from app.repositories import (
    department_repo,
    document_metadata_suggestion_repo,
    document_repo,
    document_review_repo,
    folder_repo,
    project_repo,
    tag_repo,
    user_repo,
)
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.authorization import AuthorizationScope
from app.schemas.document import (
    DocumentDetailResponse,
    DocumentListItem,
    DocumentMetadataEditRequest,
    DocumentReviewRequest,
    DocumentStatusResponse,
    DocumentSubmitRequest,
    DocumentUploadResponse,
    DocumentVisibilityResponse,
    DocumentVisibilityUser,
    MetadataSuggestionApplyRequest,
    MetadataSuggestionResponse,
)
from app.services import document_review, metadata_suggestion, type_family
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
FOLDER_WRITE_DENIED_MESSAGE = "Bu klasöre belge yükleme yetkiniz yok."
FOLDER_DEPARTMENT_MISMATCH_MESSAGE = (
    "Belgenin departmanı klasörün sahibi departmanıyla aynı olmalı."
)
DEPARTMENT_NOT_ALLOWED_MESSAGE = "Bu departmana belge yükleme yetkiniz yok."
UNKNOWN_PROJECT_MESSAGE = "Bilinmeyen proje."
NOT_READY_MESSAGE = "Belge henüz işleniyor, öneri üretilemez."
SUGGESTION_NOT_FOUND_MESSAGE = "Öneri bulunamadı."
FIELD_CANNOT_BE_NULL_MESSAGE = "Bu alan boş bırakılamaz."
INVALID_REVIEW_STATUS_MESSAGE = "Geçersiz onay durumu filtresi."
# B-28 (ADR-024): machine-readable `code` + Turkish `message` (the AI-BalBal client renders
# `detail.message`; `code` is the contract, like `product_not_enabled`).
APPROVER_NOT_CONFIGURED = {
    "code": "approver_not_configured",
    "message": "Bu departman için onaylayıcı tanımlı değil; sistem yöneticinize başvurun.",
}
SUGGESTION_PENDING = {
    "code": "suggestion_pending",
    "message": "Balbal'ın önerisi henüz hazır değil; birkaç saniye sonra tekrar deneyin.",
}
REVIEW_STATE_CONFLICT = {
    "code": "review_state_conflict",
    "message": "Belge bu işlem için uygun onay durumunda değil.",
}
NOT_THE_UPLOADER = {
    "code": "not_the_uploader",
    "message": "Yalnızca belgeyi yükleyen kişi onaya gönderebilir.",
}
NOT_THE_APPROVER = {
    "code": "not_the_approver",
    "message": "Bu belgeyi yalnızca departmanın yetkilisi onaylayabilir.",
}
COMMENT_REQUIRED = {
    "code": "comment_required",
    "message": "Geri gönderirken bir açıklama yazmalısınız.",
}
NOT_PROCESSED = {
    "code": "not_processed",
    "message": "Belge henüz işlenmedi ya da işlenemedi; onaya gönderilemez.",
}
DEPARTMENT_REQUIRED = {
    "code": "department_required",
    "message": "Belgenin departmanı belirlenmeden onaya gönderilemez.",
}
# B-28b (ADR-025): tags come from the active catalogue only; extra fields are capped and keyed
# in snake_case. The customer admin grows the catalogue — never the system.


def _unknown_tag_detail(unknown: list[str]) -> dict[str, object]:
    return {
        "code": "unknown_tag",
        "message": "Bu etiketler şirket etiket kataloğunda yok: " + ", ".join(unknown),
        "fields": ["tags"],
        "unknown": unknown,
    }


def _extra_fields_detail(reason: str) -> dict[str, object]:
    return {
        "code": "invalid_extra_fields",
        "message": "Ek alanlar kaydedilemedi: anahtar adı geçersiz ya da en fazla "
        f"{type_family.MAX_EXTRA_FIELDS} alan olabilir.",
        "fields": ["extra_fields"],
        "reason": reason,
    }


def _low_confidence_detail(fields: list[str]) -> dict[str, object]:
    return {
        "code": "low_confidence_not_confirmed",
        "message": "Düşük güvenli öneri değerleri açıkça onaylanmadan kaydedilemez: "
        + ", ".join(fields),
        "fields": fields,
    }


# Document-handling endpoints see the caller's own pending documents too (B-28, ADR-024);
# retrieval/search/ask keep the default (approved only).
_HANDLING_SCOPE = AuthorizationScope(include_pending=True)
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
        if field == "extra_fields":
            continue  # merged separately (`_apply_extra_fields`), not a column overwrite
        value = getattr(body, field)
        if value is None and field not in clearable_fields:
            raise HTTPException(422, FIELD_CANNOT_BE_NULL_MESSAGE)
        if field == "tags":
            unknown = tag_repo.unknown_tags(session, list(value or []))
            if unknown:
                raise HTTPException(422, _unknown_tag_detail(unknown))
            updates["tags"] = list(value or [])
            continue
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


# B-17: the browser gets the document title, not `original.<ext>`. Extension-keyed
# because the container's `mimetypes` knows no xlsx/xlsm (would fall to octet-stream).
MEDIA_TYPE_BY_EXTENSION: dict[str, str] = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xlsm": "application/vnd.ms-excel.sheet.macroEnabled.12",
    "csv": "text/csv; charset=utf-8",
}
# Kinds a browser renders itself; everything else is downloaded whatever `?inline` says.
INLINE_FILE_KINDS: frozenset[FileKind] = frozenset({"pdf", "image"})
DOWNLOAD_NAME_MAX_CHARS = 120
_UNSAFE_NAME_CHARS = re.compile(r'[\x00-\x1f\x7f/\\:*?"<>|]')


def download_file_name(title: str, extension: str) -> str:
    """`"Ankara RES Kredi Sözleşmesi" + "pdf"` → `Ankara RES Kredi Sözleşmesi.pdf`. Path
    separators, control and Windows-reserved characters become spaces; leading/trailing
    dots and spaces go (Windows); Turkish letters stay — Starlette percent-encodes them
    into `filename*=utf-8''…` (RFC 5987) by itself."""
    cleaned = " ".join(_UNSAFE_NAME_CHARS.sub(" ", title).split()).strip(". ")
    return f"{cleaned[:DOWNLOAD_NAME_MAX_CHARS].rstrip('. ') or 'belge'}.{extension}"


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
    folder_id: Annotated[uuid.UUID | None, Form()] = None,
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

    # B-26 (Aşama E): a document lives in a folder and its department *is* the folder
    # owner's. With `folder_id`: the caller needs write access there (owner membership or a
    # `write` grant, inherited counts; management/admin always) and `department`, if sent,
    # must agree. Without it: the department's root folder (older clients, the demo seed),
    # or no folder when there is no department either (invisible to employees, as before).
    folder = None
    if folder_id is not None:
        folder = folder_repo.get(session, folder_id)
        if folder is None:
            raise HTTPException(404, folder_repo.FOLDER_NOT_FOUND)
        owner_slug = folder.owner_department.slug
        if department is not None and department != owner_slug:
            raise HTTPException(422, FOLDER_DEPARTMENT_MISMATCH_MESSAGE)
        department = owner_slug
        if current_user.role not in (UserRole.management, UserRole.admin):
            access = folder_repo.access_map(session).access_for(
                folder.id, [d.id for d in current_user.departments]
            )
            if access not in ("owner", "write"):
                raise HTTPException(403, FOLDER_WRITE_DENIED_MESSAGE)
    elif department is not None:
        owner = department_repo.get_by_slug(session, department)
        folder = folder_repo.root_for_department(session, owner.id) if owner else None

    # Version chain (ADR-012): the predecessor must be visible to the user (ADR-004) and
    # not already superseded (chains are linear, DOMAIN_MODEL §6). Checked before the
    # file is stored so a rejected upload leaves nothing on disk.
    predecessor = None
    if supersedes_document_id is not None:
        allowed = allowed_document_ids(
            current_user, _HANDLING_SCOPE, SqlDocumentIdsProvider(session)
        )
        if supersedes_document_id not in allowed:
            raise HTTPException(404, DOCUMENT_NOT_FOUND_MESSAGE)
        predecessor = document_repo.get(session, supersedes_document_id)
        if predecessor is None:
            raise HTTPException(404, DOCUMENT_NOT_FOUND_MESSAGE)
        if predecessor.superseded_by_document_id is not None:
            raise HTTPException(409, ALREADY_SUPERSEDED_MESSAGE)

    # B-28 (ADR-024, NOT §5.2): the target department's own department_manager publishes at
    # once; everyone else — employee, management, admin, another department's manager —
    # goes through the two-stage review. Without a configured approver the upload is
    # refused before anything touches the disk (Naci SORU 1a); a department-less document
    # has no approver by definition and waits in the admin queue instead.
    review_status = document_review.initial_status(current_user, department)
    if (
        review_status != DocumentReviewStatus.approved
        and department is not None
        and not user_repo.list_department_managers(session, department)
    ):
        log.warning("upload refused: no approver", extra={"department": department})
        raise HTTPException(409, APPROVER_NOT_CONFIGURED)

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
            folder_id=folder.id if folder else None,
            review_status=review_status,
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
            folder_id=folder.id if folder else None,
            review_status=review_status,
        )
    if predecessor is not None:
        document_repo.mark_superseded(session, older=predecessor, newer=document)
    document_review_repo.add_event(
        session, document_id=document.id, actor=current_user, kind=ReviewEventKind.uploaded
    )
    if review_status == DocumentReviewStatus.approved:
        document_review_repo.add_event(
            session, document_id=document.id, actor=current_user, kind=ReviewEventKind.auto_approved
        )
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
    review_status: Annotated[str | None, Query()] = None,
) -> list[DocumentListItem]:
    """B-28: the list includes the caller's own pending documents (and a manager's review
    queue); `review_status=a,b` narrows to those states — the uploader's "my pending uploads"
    and the manager's "waiting for me" views until B-01's agenda wraps them."""
    statuses: list[DocumentReviewStatus] | None = None
    if review_status is not None:
        try:
            statuses = [DocumentReviewStatus(v.strip()) for v in review_status.split(",") if v]
        except ValueError:
            raise HTTPException(422, INVALID_REVIEW_STATUS_MESSAGE) from None
    scope = AuthorizationScope(department=department, project_id=project_id, include_pending=True)
    allowed = allowed_document_ids(current_user, scope, SqlDocumentIdsProvider(session))
    documents = document_repo.list_by_ids(session, allowed, review_statuses=statuses)
    return [DocumentListItem.model_validate(d) for d in documents]


@router.get("/{document_id}/download")
def download_document(
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    current_user: Annotated[User, Depends(get_current_user)],
    document_id: uuid.UUID,
    inline: bool = False,
) -> FileResponse:
    """403 rather than the 404 the other endpoints below use for an unauthorized id — the
    acceptance criterion text asks for 403 here specifically; a deliberate, documented
    exception to the "hide existence" pattern (docs/plans/PHASE_1_2_PLAN.md T6).

    `?inline=1` (B-17): `Content-Disposition: inline` for pdf/image so the browser shows
    the *original* file (never the OCR'd copy); workbooks/CSV are always attachments.
    `Content-Type` comes from our own map and `nosniff` is set, so the browser never
    guesses a type for user-uploaded bytes."""
    allowed = allowed_document_ids(current_user, _HANDLING_SCOPE, SqlDocumentIdsProvider(session))
    if document_id not in allowed:
        raise HTTPException(403, DOCUMENT_ACCESS_DENIED_MESSAGE)
    document = document_repo.get(session, document_id)
    if document is None:
        raise HTTPException(404, DOCUMENT_NOT_FOUND_MESSAGE)
    try:
        path = LocalFileSystemStore(settings.documents_dir).get_file(document.id, kind="original")
    except FileNotFoundError:
        raise HTTPException(404, DOCUMENT_NOT_FOUND_MESSAGE) from None
    extension = path.suffix.lstrip(".").lower()
    disposition = "inline" if inline and document.file_kind in INLINE_FILE_KINDS else "attachment"
    return FileResponse(
        path,
        filename=download_file_name(document.title, extension),
        media_type=MEDIA_TYPE_BY_EXTENSION.get(extension, "application/octet-stream"),
        content_disposition_type=disposition,
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    document_id: uuid.UUID,
) -> DocumentStatusResponse:
    allowed = allowed_document_ids(current_user, _HANDLING_SCOPE, SqlDocumentIdsProvider(session))
    if document_id not in allowed:
        raise HTTPException(404, DOCUMENT_NOT_FOUND_MESSAGE)
    document = document_repo.get(session, document_id)
    if document is None:
        raise HTTPException(404, DOCUMENT_NOT_FOUND_MESSAGE)
    return DocumentStatusResponse.model_validate(document)


def _get_authorized_document(session: Session, user: User, document_id: uuid.UUID) -> Document:
    """Detail/suggestion/edit/review lookups: the single gate with `include_pending` (B-28),
    so an uploader reaches their own pending document and a manager their queue."""
    allowed = allowed_document_ids(user, _HANDLING_SCOPE, SqlDocumentIdsProvider(session))
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
    current_user: Annotated[User, Depends(get_current_user)],
    llm: Annotated[LLMClient, Depends(get_llm_client)],
    document_id: uuid.UUID,
) -> MetadataSuggestionResponse:
    """Admin or the document's uploader (B-28 widened Phase 3.2's admin-only SORU 2 — the
    uploader needs the suggestion for stage 1). Idempotent while a suggestion is
    `pending`/`applied` — returns the existing row rather than reclassifying; a `failed` or
    `rejected` one is regenerated. The same background scan (`app/main.py` lifespan) calls
    `metadata_suggestion.suggest_metadata` directly for documents with no suggestion yet."""
    document = _get_authorized_document(session, current_user, document_id)
    if current_user.role != UserRole.admin and document.uploaded_by_id != current_user.id:
        raise HTTPException(403, NOT_THE_UPLOADER)
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
    """Admin-only metadata write. Since B-28 this is **not** the publishing act any more
    (Phase 3.2 SORU 2 superseded): publication is `submit` + `review`. Only fields present in
    `body` are written — SPEC_02 §4's "kritik alan sessiz overwrite yok" applies to every
    field uniformly. Editing an approved document drops its approval (T9)."""
    document = _get_authorized_document(session, current_user, document_id)
    suggestion = document_metadata_suggestion_repo.get_by_document_id(session, document_id)
    if suggestion is None:
        raise HTTPException(404, SUGGESTION_NOT_FOUND_MESSAGE)

    updates = _resolve_metadata_updates(
        session, body.model_fields_set, body, clearable_fields=_CLEARABLE_FIELDS
    )
    _apply_metadata_change(
        session, document, updates, current_user, extra_updates=body.extra_fields
    )
    document_metadata_suggestion_repo.mark_applied(
        session, suggestion, applied_by_id=current_user.id
    )
    session.commit()
    return DocumentListItem.model_validate(document)


def _apply_extra_fields(
    session: Session,
    document: Document,
    raw_updates: dict[str, str | None] | None,
    actor: User,
    *,
    suggested_extra: dict[str, object] | None = None,
) -> list[str]:
    """B-28b: merge staff/admin extra-field edits into `documents.extra_fields`; a key Balbal
    did not suggest is a staff addition → `field_added` event (§4.7.3). Returns changed keys."""
    try:
        updates = document_review.normalize_extra_updates(raw_updates)
    except document_review.ExtraFieldsError as exc:
        raise HTTPException(422, _extra_fields_detail(str(exc))) from None
    if not updates:
        return []
    try:
        merged, added, changed = document_review.merge_extra_fields(
            dict(document.extra_fields or {}),
            updates,
            actor_id=actor.id,
            suggested=dict(suggested_extra or {}),
            now_iso=datetime.now(UTC).isoformat(),
        )
    except document_review.ExtraFieldsError as exc:
        raise HTTPException(422, _extra_fields_detail(str(exc))) from None
    document.extra_fields = merged
    for key in added:
        document_review_repo.add_event(
            session,
            document_id=document.id,
            actor=actor,
            kind=ReviewEventKind.field_added,
            field=f"{document_review.EXTRA_PREFIX}{key}",
            after=merged[key]["value"],
        )
    session.flush()
    return changed


def _apply_metadata_change(
    session: Session,
    document: Document,
    updates: dict[str, object],
    actor: User,
    *,
    extra_updates: dict[str, str | None] | None = None,
) -> None:
    """B-28 T9: a metadata change on an approved document re-opens the review unless the
    actor is the target department's own manager (the approver editing their own call)."""
    was_approved = document.review_status == DocumentReviewStatus.approved
    before = {field: getattr(document, field) for field in updates}
    document_repo.apply_partial_update(session, document, updates)
    changed = [f for f in updates if before[f] != getattr(document, f)]
    changed += [
        f"{document_review.EXTRA_PREFIX}{k}"
        for k in _apply_extra_fields(session, document, extra_updates, actor)
    ]
    if not (was_approved and changed):
        return
    if document_review.is_target_manager(actor, document.department):
        return
    document.review_status = DocumentReviewStatus.pending_review
    document.review_comment = None
    document_review_repo.add_event(
        session,
        document_id=document.id,
        actor=actor,
        kind=ReviewEventKind.metadata_changed_after_approval,
        field=",".join(sorted(changed)),
    )
    session.flush()


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
    _apply_metadata_change(
        session, document, updates, current_user, extra_updates=body.extra_fields
    )
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
    grantee_slugs: frozenset[str] = frozenset()
    if document.folder_id is not None:
        slugs = {d.id: d.slug for d in department_repo.list_all(session)}
        grantee_ids = folder_repo.access_map(session).grantee_department_ids(document.folder_id)
        grantee_slugs = frozenset(slugs[i] for i in grantee_ids if i in slugs)
    provider = SingleDocumentIdsProvider(document, folder_grantee_slugs=grantee_slugs)
    # B-28: a pending document is "seen" by whoever may handle it (uploader, target
    # department's manager, admin); an approved one by the normal rule.
    scope = (
        _HANDLING_SCOPE
        if document.review_status != DocumentReviewStatus.approved
        else AuthorizationScope()
    )
    visible_users = [
        user
        for user in user_repo.list_all(session)
        if document.id in allowed_document_ids(user, scope, provider)
    ]
    return DocumentVisibilityResponse(
        document_id=document.id,
        department=document.department,
        confidentiality=document.confidentiality,
        review_status=document.review_status,
        users=[DocumentVisibilityUser.model_validate(user) for user in visible_users],
    )


# ------------------------------------------------------------------ B-28 two-stage review


@router.post("/{document_id}/submit", response_model=DocumentDetailResponse)
def submit_document(
    document_id: uuid.UUID,
    body: DocumentSubmitRequest,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DocumentDetailResponse:
    """Stage 1 (ADR-024): the uploader — nobody else, not even admin (P-1) — confirms the
    final metadata. A kept suggestion below `metadata_confirm_threshold` must be listed in
    `confirmed_fields` (BACKEND_GAPS §4.7.5). OCR-family documents need their suggestion to
    exist first (409 `suggestion_pending` while the background scan is still working); a
    workbook has no suggestion and is confirmed from the typed fields alone."""
    document = _get_authorized_document(session, current_user, document_id)
    if document.uploaded_by_id != current_user.id:
        raise HTTPException(403, NOT_THE_UPLOADER)
    if document.review_status not in document_review.SUBMITTABLE:
        raise HTTPException(409, REVIEW_STATE_CONFLICT)
    suggestion = document_metadata_suggestion_repo.get_by_document_id(session, document_id)
    is_workbook = document.storage_extension in EXCEL_EXTENSIONS
    if not is_workbook:
        if document.ingestion_status == IngestionStatus.failed:
            raise HTTPException(409, NOT_PROCESSED)
        if document.ingestion_status != IngestionStatus.ready or suggestion is None:
            raise HTTPException(409, SUGGESTION_PENDING)

    provided = sorted(body.model_fields_set - {"confirmed_fields", "extra_fields"})
    updates = _resolve_metadata_updates(
        session, set(provided), body, clearable_fields=_CLEARABLE_FIELDS
    )
    final_values: dict[str, object] = {field: getattr(body, field) for field in provided}
    # B-28b: extra fields join the same confidence rule under `extra_fields.<key>`.
    try:
        extra_updates = document_review.normalize_extra_updates(body.extra_fields)
    except document_review.ExtraFieldsError as exc:
        raise HTTPException(422, _extra_fields_detail(str(exc))) from None
    for key, value in sorted(extra_updates.items()):
        if value is not None:
            final_values[f"{document_review.EXTRA_PREFIX}{key}"] = value
    suggested_flat = document_review.flatten_suggestion(
        suggestion.fields if suggestion is not None else None
    )
    outcomes = document_review.classify_fields(
        suggested_flat,
        final_values,
        set(body.confirmed_fields),
        settings.metadata_confirm_threshold,
    )
    missing = document_review.unconfirmed_low_confidence(outcomes)
    if missing:
        raise HTTPException(422, _low_confidence_detail(missing))
    final_department = updates.get("department", document.department)
    if final_department is None:
        # No department → no approver, ever; the uploader (or admin, via PATCH) must place
        # the document first. Keeps "pending with nobody to approve" from existing.
        raise HTTPException(422, DEPARTMENT_REQUIRED)

    resubmission = document.review_status == DocumentReviewStatus.changes_requested
    document_repo.apply_partial_update(session, document, updates)
    _apply_extra_fields(
        session,
        document,
        extra_updates,
        current_user,
        suggested_extra=(suggestion.fields.get("extra_fields") if suggestion is not None else None),
    )
    for outcome in outcomes:
        if outcome.edited and outcome.suggested is not None:
            kind = ReviewEventKind.field_edited
        elif outcome.low_confidence and outcome.confirmed:
            kind = ReviewEventKind.field_confirmed
        else:
            continue
        document_review_repo.add_event(
            session,
            document_id=document.id,
            actor=current_user,
            kind=kind,
            field=outcome.field,
            before=outcome.suggested,
            after=outcome.final,
            confidence=outcome.confidence,
        )
    if suggestion is not None and suggestion.status in (
        SuggestionStatus.pending,
        SuggestionStatus.rejected,
        SuggestionStatus.failed,
    ):
        document_metadata_suggestion_repo.mark_applied(
            session, suggestion, applied_by_id=current_user.id
        )
    document.review_status = document_review.status_after_submit(current_user, document.department)
    document.review_comment = None
    document.submitted_at = datetime.now(UTC)
    document_review_repo.add_event(
        session,
        document_id=document.id,
        actor=current_user,
        kind=ReviewEventKind.resubmitted if resubmission else ReviewEventKind.submitted,
    )
    if document.review_status == DocumentReviewStatus.approved:
        document_review_repo.add_event(
            session, document_id=document.id, actor=current_user, kind=ReviewEventKind.auto_approved
        )
    session.commit()
    return DocumentDetailResponse.model_validate(document)


@router.post("/{document_id}/review", response_model=DocumentDetailResponse)
def review_document(
    document_id: uuid.UUID,
    body: DocumentReviewRequest,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DocumentDetailResponse:
    """Stage 2 (ADR-024, NOT §5.2): only the target department's own `department_manager`
    decides — `management`/`admin` and other departments' managers get 403."""
    document = _get_authorized_document(session, current_user, document_id)
    if not document_review.is_target_manager(current_user, document.department):
        raise HTTPException(403, NOT_THE_APPROVER)
    if document.review_status != DocumentReviewStatus.pending_review:
        raise HTTPException(409, REVIEW_STATE_CONFLICT)
    comment = body.comment.strip() if body.comment else None
    if body.decision == "approve":
        document.review_status = DocumentReviewStatus.approved
        kind = ReviewEventKind.approved
    else:
        if not comment:
            raise HTTPException(422, COMMENT_REQUIRED)
        document.review_status = DocumentReviewStatus.changes_requested
        kind = ReviewEventKind.changes_requested
    document.review_comment = comment
    document.reviewed_at = datetime.now(UTC)
    document.reviewed_by_id = current_user.id
    document_review_repo.add_event(
        session, document_id=document.id, actor=current_user, kind=kind, comment=comment
    )
    session.commit()
    return DocumentDetailResponse.model_validate(document)
