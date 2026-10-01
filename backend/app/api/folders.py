"""Folders and department access grants (B-26, ADR-023, Aşama E).

`/api/admin/folders*` — the customer's own system administrator builds the tree and grants
(Tansu, 01.10.2026: "hepsini bizim oluşturacağımız araçtan admin belirler"). `/api/folders` —
what the signed-in user can see, with their effective access. Grants never grant anything
by themselves: they are read by `allowed_document_ids` through the provider (ADR-004).
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.db import get_session
from app.models.folder import Folder, FolderAccess
from app.models.user import User, UserRole
from app.repositories import department_repo, folder_repo
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.authorization import AuthorizationScope
from app.schemas.folder import (
    AdminFolderResponse,
    FolderAuditEntryResponse,
    FolderCreateRequest,
    FolderGrantResponse,
    FolderGrantsUpdateRequest,
    FolderUpdateRequest,
    UserFolderResponse,
)
from app.services.authorization import allowed_document_ids
from app.services.folder_access import FolderAccessMap

admin_router = APIRouter(prefix="/api/admin/folders", tags=["folders"])
user_router = APIRouter(prefix="/api/folders", tags=["folders"])


def _get_folder(session: Session, folder_id: uuid.UUID) -> Folder:
    folder = folder_repo.get(session, folder_id)
    if folder is None:
        raise HTTPException(404, folder_repo.FOLDER_NOT_FOUND)
    return folder


def _admin_response(
    folder: Folder,
    access: FolderAccessMap,
    slugs: dict[uuid.UUID, str],
    counts: dict[uuid.UUID, int],
) -> AdminFolderResponse:
    return AdminFolderResponse(
        id=folder.id,
        name=folder.name,
        parent_id=folder.parent_id,
        owner_department_slug=slugs[folder.owner_department_id],
        grants=[
            FolderGrantResponse(
                department_slug=slugs[g.department_id], access=g.access, inherited=g.inherited
            )
            for g in access.effective_grants(folder.id)
            if g.department_id in slugs
        ],
        document_count=counts.get(folder.id, 0),
    )


def _slugs(session: Session) -> dict[uuid.UUID, str]:
    return {d.id: d.slug for d in department_repo.list_all(session)}


@admin_router.get("", response_model=list[AdminFolderResponse])
def list_folders_admin(
    session: Annotated[Session, Depends(get_session)],
    _admin: Annotated[User, Depends(require_admin)],
) -> list[AdminFolderResponse]:
    folders = folder_repo.list_all(session)
    access = FolderAccessMap(folders, folder_repo.list_grants(session))
    slugs, counts = _slugs(session), folder_repo.document_counts(session)
    return [_admin_response(f, access, slugs, counts) for f in folders]


@admin_router.post("", response_model=AdminFolderResponse, status_code=201)
def create_folder(
    body: FolderCreateRequest,
    session: Annotated[Session, Depends(get_session)],
    _admin: Annotated[User, Depends(require_admin)],
) -> AdminFolderResponse:
    owner = department_repo.get_by_slug(session, body.owner_department_slug)
    if owner is None:
        raise HTTPException(404, folder_repo.DEPARTMENT_NOT_FOUND)
    try:
        folder = folder_repo.create(
            session, name=body.name, parent_id=body.parent_id, owner_department=owner
        )
    except folder_repo.FolderError as exc:
        raise HTTPException(exc.status, exc.message) from None
    session.commit()
    return _admin_response(folder, folder_repo.access_map(session), _slugs(session), {})


@admin_router.patch("/{folder_id}", response_model=AdminFolderResponse)
def update_folder(
    folder_id: uuid.UUID,
    body: FolderUpdateRequest,
    session: Annotated[Session, Depends(get_session)],
    _admin: Annotated[User, Depends(require_admin)],
) -> AdminFolderResponse:
    folder = _get_folder(session, folder_id)
    try:
        folder_repo.update(
            session,
            folder,
            name=body.name,
            parent_id=body.parent_id,
            parent_given="parent_id" in body.model_fields_set,
        )
    except folder_repo.FolderError as exc:
        raise HTTPException(exc.status, exc.message) from None
    session.commit()
    return _admin_response(
        folder,
        folder_repo.access_map(session),
        _slugs(session),
        folder_repo.document_counts(session),
    )


@admin_router.delete("/{folder_id}", status_code=204)
def delete_folder(
    folder_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
    _admin: Annotated[User, Depends(require_admin)],
) -> None:
    folder = _get_folder(session, folder_id)
    try:
        folder_repo.delete(session, folder)
    except folder_repo.FolderError as exc:
        raise HTTPException(exc.status, exc.message) from None
    session.commit()


@admin_router.put("/{folder_id}/grants", response_model=AdminFolderResponse)
def set_folder_grants(
    folder_id: uuid.UUID,
    body: FolderGrantsUpdateRequest,
    session: Annotated[Session, Depends(get_session)],
    admin: Annotated[User, Depends(require_admin)],
) -> AdminFolderResponse:
    """Writes this folder's own definitions in one go; `none` removes a definition so the
    parent's applies again. Every effective change is one `folder_grant_events` row."""
    folder = _get_folder(session, folder_id)
    departments = {d.slug: d for d in department_repo.list_all(session)}
    desired: dict[uuid.UUID, str] = {}
    for choice in body.grants:
        department = departments.get(choice.department_slug)
        if department is None:
            raise HTTPException(404, folder_repo.DEPARTMENT_NOT_FOUND)
        desired[department.id] = choice.access
    try:
        folder_repo.set_grants(
            session,
            folder,
            desired,  # type: ignore[arg-type]
            actor=admin,
            departments={d.id: d for d in departments.values()},
        )
    except folder_repo.FolderError as exc:
        raise HTTPException(exc.status, exc.message) from None
    session.commit()
    return _admin_response(
        folder,
        folder_repo.access_map(session),
        _slugs(session),
        folder_repo.document_counts(session),
    )


@admin_router.get("/audit", response_model=list[FolderAuditEntryResponse])
def list_folder_audit(
    session: Annotated[Session, Depends(get_session)],
    _admin: Annotated[User, Depends(require_admin)],
    limit: Annotated[int, Query(ge=1, le=folder_repo.EVENTS_LIMIT_MAX)] = 100,
) -> list[FolderAuditEntryResponse]:
    return [
        FolderAuditEntryResponse.model_validate(e)
        for e in folder_repo.list_events(session, limit=limit)
    ]


@user_router.get("", response_model=list[UserFolderResponse])
def list_my_folders(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[UserFolderResponse]:
    """Folders the user can see: owned by one of their departments (`write`), or reachable
    through a grant (effective access). `management`/`admin` see every folder with `write`.
    `document_count` is the number of documents *this user* can see in the folder."""
    folders = folder_repo.list_all(session)
    access = FolderAccessMap(folders, folder_repo.list_grants(session))
    slugs = _slugs(session)
    allowed = allowed_document_ids(
        current_user, AuthorizationScope(), SqlDocumentIdsProvider(session)
    )
    counts = folder_repo.document_counts(session, within_ids=allowed)
    member_ids = [d.id for d in current_user.departments]
    result: list[UserFolderResponse] = []
    for folder in folders:
        if current_user.role in (UserRole.admin, UserRole.management):
            level = FolderAccess.write
        else:
            effective = access.access_for(folder.id, member_ids)
            if effective == "none":
                continue
            level = FolderAccess.read if effective == "read" else FolderAccess.write
        result.append(
            UserFolderResponse(
                id=folder.id,
                name=folder.name,
                parent_id=folder.parent_id,
                owner_department_slug=slugs[folder.owner_department_id],
                access=level,
                document_count=counts.get(folder.id, 0),
            )
        )
    return result
