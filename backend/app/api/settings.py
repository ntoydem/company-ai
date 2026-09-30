"""`GET/PATCH /api/admin/settings` — the product layer key (B-25, ADR-022), admin-only.
The CLI equivalent is `python -m app.cli set-enabled-products`."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.db import get_session
from app.models.user import User
from app.repositories import company_settings_repo
from app.schemas.settings import CompanySettingsResponse, CompanySettingsUpdate

router = APIRouter(prefix="/api/admin/settings", tags=["settings"])


@router.get("", response_model=CompanySettingsResponse)
def get_company_settings(
    session: Annotated[Session, Depends(get_session)],
    _admin: Annotated[User, Depends(require_admin)],
) -> CompanySettingsResponse:
    return CompanySettingsResponse(enabled_products=company_settings_repo.enabled_products(session))


@router.patch("", response_model=CompanySettingsResponse)
def update_company_settings(
    body: CompanySettingsUpdate,
    session: Annotated[Session, Depends(get_session)],
    _admin: Annotated[User, Depends(require_admin)],
) -> CompanySettingsResponse:
    company_settings_repo.set_enabled_products(session, body.enabled_products)
    return CompanySettingsResponse(enabled_products=company_settings_repo.enabled_products(session))
