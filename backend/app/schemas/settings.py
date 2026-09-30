"""`GET/PATCH /api/admin/settings` — the product layer key (B-25), editable by the
customer's admin (Tansu #2, docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md §5.1)."""

from pydantic import BaseModel, Field, field_validator

from app.models.company_settings import PRODUCT_LEVELS, ProductLevel


class CompanySettingsResponse(BaseModel):
    enabled_products: list[ProductLevel]


class CompanySettingsUpdate(BaseModel):
    enabled_products: list[ProductLevel] = Field(min_length=1)

    @field_validator("enabled_products")
    @classmethod
    def _canonical_order(cls, value: list[ProductLevel]) -> list[ProductLevel]:
        enabled = set(value)
        return [level for level in PRODUCT_LEVELS if level in enabled]
