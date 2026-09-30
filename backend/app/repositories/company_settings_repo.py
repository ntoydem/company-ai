"""`company_settings` — the single row migration 0009 creates. Read on every request that
needs it (`/login`, `/me`, `/api/ask`, product-gated endpoints): one primary-key lookup,
no cache, so a change is visible immediately."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.company_settings import (
    PRODUCT_LEVELS,
    SETTINGS_ROW_ID,
    CompanySettings,
    ProductLevel,
)


class CompanySettingsMissingError(RuntimeError):
    """The row is guaranteed by migration 0009; its absence is a deployment error, never
    something to paper over with a default."""


def get(session: Session) -> CompanySettings:
    row = session.get(CompanySettings, SETTINGS_ROW_ID)
    if row is None:
        raise CompanySettingsMissingError("company_settings row missing — run alembic upgrade head")
    return row


def enabled_products(session: Session) -> list[ProductLevel]:
    """Normalised to the canonical `P1, P2, P3` order."""
    enabled = set(get(session).enabled_products)
    return [level for level in PRODUCT_LEVELS if level in enabled]


def set_enabled_products(session: Session, products: list[ProductLevel]) -> CompanySettings:
    row = get(session)
    row.enabled_products = [level for level in PRODUCT_LEVELS if level in set(products)]
    session.commit()
    return row
