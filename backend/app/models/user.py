import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.department import Department


class UserRole(enum.StrEnum):
    admin = "admin"
    management = "management"
    # B-08 (02.10.2026): a department's manager — own departments at `normal` and
    # `restricted`, never `board`; assigned per person by the customer admin (NOT §8.1).
    department_manager = "department_manager"
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
    # B-05 (Aşama C): job title for the directory and approval screens. `manager_id` is
    # deliberately absent until B-22 needs it.
    title: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # B-09 (Aşama C): the person's home department (P-5). Must be one of the memberships;
    # NULL for management/admin, who have no membership rows. Not an authorization input.
    primary_department_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    primary_department: Mapped[Department | None] = relationship(
        "Department", foreign_keys=[primary_department_id]
    )

    # Membership (SPEC_02 §5, Phase 1.2): grants an `employee` visibility into a
    # department's `normal` documents. `management`/`admin` don't need rows here — see
    # app/services/authorization.py.
    departments: Mapped[list[Department]] = relationship("Department", secondary="user_departments")

    def ordered_departments(self) -> list[Department]:
        """Memberships with the primary department first, the rest by slug. The AI-BalBal
        frontend treats `department_slugs[0]` as the home department, so this ordering makes
        B-09 effective there without a frontend change."""
        return sorted(
            self.departments,
            key=lambda d: (d.id != self.primary_department_id, d.slug),
        )

    @property
    def department_ids(self) -> list[uuid.UUID]:
        """`ProjectResponse.department_ids` ile simetrik (Phase 5.2): admin kullanıcı
        formunun departman checkbox'larını önceden işaretlemesi için."""
        return [department.id for department in self.ordered_departments()]

    @property
    def department_slugs(self) -> list[str]:
        """Direct membership slugs only (empty for admin/management, who need no rows —
        SPEC_02 §5), primary department first. Exposed via `/api/auth/me` so the UI can
        hide department cards (Phase 3.3); hiding is convenience, the gate stays
        server-side (ADR-004)."""
        return [department.slug for department in self.ordered_departments()]

    @property
    def primary_department_slug(self) -> str | None:
        return self.primary_department.slug if self.primary_department is not None else None

    def __repr__(self) -> str:  # never include password_hash
        return f"User(username={self.username!r}, role={self.role.value!r})"
