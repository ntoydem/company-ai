"""One-row company settings (B-25, ADR-022): which product layers this installation has
enabled. Data, not configuration — the customer's admin changes it at runtime, so it is
neither an env variable nor a code constant (P-8)."""

from datetime import datetime
from typing import Literal, get_args

from sqlalchemy import CheckConstraint, DateTime, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

ProductLevel = Literal["P1", "P2", "P3"]
PRODUCT_LEVELS: tuple[ProductLevel, ...] = get_args(ProductLevel)
# Demo default: every layer open (BACKEND_GAPS §1.5.4). The row itself is inserted by
# migration 0009; the application never creates it silently.
DEFAULT_ENABLED_PRODUCTS: list[ProductLevel] = list(PRODUCT_LEVELS)
SETTINGS_ROW_ID = 1


class CompanySettings(Base):
    __tablename__ = "company_settings"
    __table_args__ = (
        CheckConstraint(f"id = {SETTINGS_ROW_ID}", name="company_settings_single_row"),
    )

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, default=SETTINGS_ROW_ID)
    enabled_products: Mapped[list[str]] = mapped_column(
        ARRAY(String(2)), nullable=False, server_default="{P1,P2,P3}"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"CompanySettings(enabled_products={self.enabled_products!r})"
