import uuid

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Department(TimestampMixin, Base):
    """Organisation tree (SPEC_02 §8): Enerji Grubu (+ Geliştirme/EPC-İnşaat/Bakım),
    Finans, Hukuk, Mali İşler, İdari İşler. `parent_id` is null for top-level departments.
    No `is_active` — there is no department CRUD in V0 (docs/plans/PHASE_1_2_PLAN.md)."""

    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128))
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True
    )

    def __repr__(self) -> str:
        return f"Department(slug={self.slug!r})"
