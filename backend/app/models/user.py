import enum
import uuid

from sqlalchemy import Boolean, Enum, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.department import Department


class UserRole(enum.StrEnum):
    admin = "admin"
    management = "management"
    employee = "employee"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(128))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda e: [m.value for m in e]),
        default=UserRole.employee,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    # SSO readiness (SPEC_02 §7): V0 uses only "local".
    auth_provider: Mapped[str] = mapped_column(String(32), default="local", server_default="local")
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Membership (SPEC_02 §5, Phase 1.2): grants an `employee` visibility into a
    # department's `normal` documents. `management`/`admin` don't need rows here — see
    # app/services/authorization.py.
    departments: Mapped[list[Department]] = relationship("Department", secondary="user_departments")

    @property
    def department_slugs(self) -> list[str]:
        """Direct membership slugs only (empty for admin/management, who need no rows —
        SPEC_02 §5). Exposed via `/api/auth/me` so the UI can hide department cards
        (Phase 3.3); hiding is convenience, the gate stays server-side (ADR-004)."""
        return [department.slug for department in self.departments]

    def __repr__(self) -> str:  # never include password_hash
        return f"User(username={self.username!r}, role={self.role.value!r})"
