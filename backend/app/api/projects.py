"""Admin project CRUD (SPEC_02 §6, Phase 1.2). Reading the list is open to every
authenticated user — employees need it to filter documents/questions; only create and
update are admin-only."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.db import get_session
from app.models.user import User
from app.repositories import department_repo, project_repo
from app.schemas.project import ProjectCreateRequest, ProjectResponse, ProjectUpdateRequest

router = APIRouter(prefix="/api/projects", tags=["projects"])

PROJECT_NOT_FOUND_MESSAGE = "Proje bulunamadı."
PROJECT_CODE_EXISTS_MESSAGE = "Bu proje kodu zaten kullanılıyor."
DEPARTMENT_NOT_FOUND_MESSAGE = "Departman bulunamadı."


def _check_department_ids(session: Session, department_ids: list[uuid.UUID]) -> None:
    if not department_repo.all_exist(session, department_ids):
        raise HTTPException(404, DEPARTMENT_NOT_FOUND_MESSAGE)


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ProjectResponse]:
    return [ProjectResponse.model_validate(p) for p in project_repo.list_all(session)]


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(
    body: ProjectCreateRequest,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_admin)],
) -> ProjectResponse:
    if project_repo.get_by_code(session, body.code) is not None:
        raise HTTPException(409, PROJECT_CODE_EXISTS_MESSAGE)
    _check_department_ids(session, body.department_ids)
    project = project_repo.create(
        session,
        name=body.name,
        code=body.code,
        stage=body.stage,
        department_ids=body.department_ids,
    )
    session.commit()
    return ProjectResponse.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdateRequest,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_admin)],
) -> ProjectResponse:
    project = project_repo.get(session, project_id)
    if project is None:
        raise HTTPException(404, PROJECT_NOT_FOUND_MESSAGE)
    if body.department_ids is not None:
        _check_department_ids(session, body.department_ids)
    project = project_repo.update(
        session,
        project,
        name=body.name,
        stage=body.stage,
        is_active=body.is_active,
        department_ids=body.department_ids,
    )
    session.commit()
    return ProjectResponse.model_validate(project)
