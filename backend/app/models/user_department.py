import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserDepartment(Base):
    """`User` ⟷ `Department` membership (SPEC_02 §5). A user may belong to several
    departments; membership alone grants an `employee` visibility into that department's
    `normal` documents (see `app/services/authorization.py`). `management`/`admin` need
    no rows here — they see every department regardless of membership."""

    __tablename__ = "user_departments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
