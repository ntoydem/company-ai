"""`folders`, `folder_grants`, `folder_grant_events` persistence (B-26, ADR-023)."""

from __future__ import annotations

import uuid
from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.document import Document
from app.models.folder import Folder, FolderAccess, FolderGrant, FolderGrantEvent
from app.models.user import User
from app.services.folder_access import Access, FolderAccessMap

EVENTS_LIMIT_MAX = 500


class FolderError(ValueError):
    """Rule violation the API maps to 4xx; `status` says which."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


# User-facing messages (Turkish, ADR-017).
FOLDER_NOT_FOUND = "Klasör bulunamadı."
PARENT_NOT_FOUND = "Üst klasör bulunamadı."
DEPARTMENT_NOT_FOUND = "Departman bulunamadı."
OWNER_MUST_MATCH_PARENT = "Alt klasörün sahibi departmanı üst klasörle aynı olmalı."
DUPLICATE_NAME = "Aynı üst klasörde bu adda bir klasör zaten var."
CANNOT_MOVE_INTO_SUBTREE = "Klasör kendi altına taşınamaz."
NOT_EMPTY = "Klasör boş değil: içinde belge veya alt klasör var."
OWNER_CANNOT_BE_GRANTED = (
    "Sahibi departmana ayrıca yetki verilemez; sahibi her zaman değiştirebilir."
)


def get(session: Session, folder_id: uuid.UUID) -> Folder | None:
    return session.get(Folder, folder_id)


def list_all(session: Session) -> list[Folder]:
    return list(session.scalars(select(Folder).order_by(Folder.name, Folder.id)).all())


def list_grants(session: Session) -> list[FolderGrant]:
    return list(session.scalars(select(FolderGrant)).all())


def access_map(session: Session) -> FolderAccessMap:
    return FolderAccessMap(list_all(session), list_grants(session))


def root_for_department(session: Session, department_id: uuid.UUID) -> Folder | None:
    return session.scalar(
        select(Folder)
        .where(Folder.parent_id.is_(None), Folder.owner_department_id == department_id)
        .order_by(Folder.created_at)
    )


def _name_taken(
    session: Session, *, parent_id: uuid.UUID | None, name: str, exclude: uuid.UUID | None
) -> bool:
    stmt = select(Folder.id).where(Folder.name == name)
    stmt = stmt.where(
        Folder.parent_id.is_(None) if parent_id is None else Folder.parent_id == parent_id
    )
    if exclude is not None:
        stmt = stmt.where(Folder.id != exclude)
    return session.scalar(stmt) is not None


def create(
    session: Session, *, name: str, parent_id: uuid.UUID | None, owner_department: Department
) -> Folder:
    if parent_id is not None:
        parent = get(session, parent_id)
        if parent is None:
            raise FolderError(404, PARENT_NOT_FOUND)
        if parent.owner_department_id != owner_department.id:
            raise FolderError(422, OWNER_MUST_MATCH_PARENT)
    if _name_taken(session, parent_id=parent_id, name=name, exclude=None):
        raise FolderError(409, DUPLICATE_NAME)
    folder = Folder(name=name, parent_id=parent_id, owner_department_id=owner_department.id)
    session.add(folder)
    session.flush()
    return folder


def update(
    session: Session,
    folder: Folder,
    *,
    name: str | None,
    parent_id: uuid.UUID | None,
    parent_given: bool,
) -> Folder:
    new_parent_id = parent_id if parent_given else folder.parent_id
    if parent_given and parent_id is not None:
        parent = get(session, parent_id)
        if parent is None:
            raise FolderError(404, PARENT_NOT_FOUND)
        if parent.owner_department_id != folder.owner_department_id:
            raise FolderError(422, OWNER_MUST_MATCH_PARENT)
        if parent_id in access_map(session).subtree_ids(folder.id):
            raise FolderError(422, CANNOT_MOVE_INTO_SUBTREE)
    new_name = name if name is not None else folder.name
    if _name_taken(session, parent_id=new_parent_id, name=new_name, exclude=folder.id):
        raise FolderError(409, DUPLICATE_NAME)
    folder.name = new_name
    folder.parent_id = new_parent_id
    session.flush()
    return folder


def delete(session: Session, folder: Folder) -> None:
    has_children = session.scalar(select(Folder.id).where(Folder.parent_id == folder.id))
    has_documents = session.scalar(select(Document.id).where(Document.folder_id == folder.id))
    if has_children is not None or has_documents is not None:
        raise FolderError(409, NOT_EMPTY)
    session.delete(folder)
    session.flush()


def set_grants(
    session: Session,
    folder: Folder,
    desired: dict[uuid.UUID, Access],
    *,
    actor: User,
    departments: dict[uuid.UUID, Department],
) -> list[FolderGrantEvent]:
    """Replace the folder's *own* definitions: `desired` maps department id → none|read|write
    (`none` removes the definition so inheritance applies again). One event per department
    whose *effective* access actually changed, with before/after as effective values."""
    if folder.owner_department_id in desired:
        raise FolderError(422, OWNER_CANNOT_BE_GRANTED)
    before_map = access_map(session)
    before = {
        d: before_map.access_for(folder.id, [d]) for d in desired
    }  # "owner" impossible here (checked above)
    own = {g.department_id: g for g in folder.grants}
    for department_id, access in desired.items():
        existing = own.get(department_id)
        if access == "none":
            if existing is not None:
                session.delete(existing)
        elif existing is None:
            session.add(
                FolderGrant(
                    folder_id=folder.id, department_id=department_id, access=FolderAccess(access)
                )
            )
        else:
            existing.access = FolderAccess(access)
    session.flush()
    session.expire(folder, ["grants"])
    after_map = access_map(session)
    events: list[FolderGrantEvent] = []
    for department_id in desired:
        new = after_map.access_for(folder.id, [department_id])
        if new == before[department_id]:
            continue
        department = departments[department_id]
        event = FolderGrantEvent(
            actor_user_id=actor.id,
            actor_name=actor.display_name,
            folder_id=folder.id,
            folder_name=folder.name,
            department_id=department.id,
            department_slug=department.slug,
            before=before[department_id],
            after=new,
        )
        session.add(event)
        events.append(event)
    session.flush()
    return events


def list_events(session: Session, *, limit: int) -> list[FolderGrantEvent]:
    stmt = (
        select(FolderGrantEvent)
        .order_by(FolderGrantEvent.created_at.desc(), FolderGrantEvent.id)
        .limit(min(limit, EVENTS_LIMIT_MAX))
    )
    return list(session.scalars(stmt).all())


def document_counts(
    session: Session, *, within_ids: Iterable[uuid.UUID] | None = None
) -> dict[uuid.UUID, int]:
    """Documents per folder (the folder itself, not its subtree); `within_ids` restricts
    to the caller's allowed documents for the per-user view."""
    stmt = (
        select(Document.folder_id, func.count(Document.id))
        .where(Document.folder_id.is_not(None))
        .group_by(Document.folder_id)
    )
    if within_ids is not None:
        ids = list(within_ids)
        if not ids:
            return {}
        stmt = stmt.where(Document.id.in_(ids))
    return {folder_id: int(count) for folder_id, count in session.execute(stmt).all()}
