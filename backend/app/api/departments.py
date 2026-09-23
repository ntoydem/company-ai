"""`GET /api/departments` — read-only department list (SPEC_02 §8, Phase 1.2).

No CRUD: departments are seed-only in V0 (docs/plans/PHASE_1_2_PLAN.md). This endpoint
exists so the admin project form can offer department choices."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.user import User
from app.repositories import department_repo
from app.schemas.department import DepartmentResponse

router = APIRouter(prefix="/api/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentResponse])
def list_departments(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[DepartmentResponse]:
    return [DepartmentResponse.model_validate(d) for d in department_repo.list_all(session)]
