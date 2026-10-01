"""Folders and department access grants (B-26, ADR-023, Aşama E).

The folder tree is customer data (P-8): the company's own admin builds it from the admin
screen; the seed only creates one root folder per top-level department. A document lives
in exactly one folder and its `department` is the folder owner's slug (ADR-004: permission
still derives from department). Grants give *another* department `read` or `write` on a
folder; a sub-folder inherits the nearest ancestor's definition unless it has its own.
Grants only ever feed `allowed_document_ids` — no second permission engine.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.department import Department


class FolderAccess(enum.StrEnum):
    read = "read"
    write = "write"


class Folder(TimestampMixin, Base):
    __tablename__ = "folders"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128))
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("folders.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    # A sub-folder's owner always equals its parent's (enforced in folder_repo).
    owner_department_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), index=True
    )
    owner_department: Mapped[Department] = relationship("Department")
    grants: Mapped[list["FolderGrant"]] = relationship(
        "FolderGrant", cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"Folder(name={self.name!r})"


class FolderGrant(Base):
    __tablename__ = "folder_grants"

    folder_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("folders.id", ondelete="CASCADE"), primary_key=True
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    access: Mapped[FolderAccess] = mapped_column(
        Enum(FolderAccess, name="folder_access", values_callable=lambda e: [m.value for m in e])
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class FolderGrantEvent(Base):
    """Who changed which department's access on which folder, from what to what (BACKEND_GAPS
    §2.6.1/8). Not `audit_log` — that table records questions (ADR-016). `folder_name` and
    `department_slug` are copied so the row still reads after a folder/department is gone."""

    __tablename__ = "folder_grant_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    actor_name: Mapped[str] = mapped_column(String(128))
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("folders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    folder_name: Mapped[str] = mapped_column(String(128))
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    department_slug: Mapped[str] = mapped_column(String(64))
    # Effective values (inheritance included): "none" | "read" | "write".
    before: Mapped[str] = mapped_column(String(5))
    after: Mapped[str] = mapped_column(String(5))
