"""Admin user management (Phase 5.2, SPEC_06 §2): create, list, edit role/active status
and department membership. Password reset and department-tree CRUD are deliberately out
of scope here (SORU 2/4, docs/plans/PHASE_5_2_PLAN.md)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.db import get_session
from app.models.user import User, UserRole
from app.repositories import department_repo, user_repo
from app.schemas.user import UserCreateRequest, UserResponse, UserUpdateRequest
from app.services.security import hash_password

router = APIRouter(prefix="/api/users", tags=["users"])

USER_NOT_FOUND_MESSAGE = "Kullanıcı bulunamadı."
USERNAME_EXISTS_MESSAGE = "Bu kullanıcı adı zaten kullanılıyor."
DEPARTMENT_NOT_FOUND_MESSAGE = "Departman bulunamadı."
CANNOT_DEMOTE_OR_DISABLE_SELF_MESSAGE = (
    "Kendi hesabınızın rolünü düşüremez veya devre dışı bırakamazsınız."
)
PRIMARY_DEPARTMENT_NOT_A_MEMBERSHIP_MESSAGE = (
    "Ana departman, kullanıcının üyeliklerinden biri olmalı."
)


def _check_department_ids(session: Session, department_ids: list[uuid.UUID]) -> None:
    if not department_repo.all_exist(session, department_ids):
        raise HTTPException(404, DEPARTMENT_NOT_FOUND_MESSAGE)


@router.get("", response_model=list[UserResponse])
def list_users(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_admin)],
) -> list[UserResponse]:
    return [UserResponse.model_validate(u) for u in user_repo.list_all(session)]


@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    body: UserCreateRequest,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_admin)],
) -> UserResponse:
    if user_repo.get_by_username(session, body.username) is not None:
        raise HTTPException(409, USERNAME_EXISTS_MESSAGE)
    _check_department_ids(session, body.department_ids)
    try:
        user = user_repo.create(
            session,
            username=body.username,
            password_hash=hash_password(body.password),
            display_name=body.display_name,
            role=body.role,
            department_ids=body.department_ids,
            title=body.title,
            primary_department_id=body.primary_department_id,
        )
    except user_repo.PrimaryDepartmentNotAMembershipError:
        raise HTTPException(422, PRIMARY_DEPARTMENT_NOT_A_MEMBERSHIP_MESSAGE) from None
    session.commit()
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: uuid.UUID,
    body: UserUpdateRequest,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_admin)],
) -> UserResponse:
    user = user_repo.get_by_id(session, user_id)
    if user is None:
        raise HTTPException(404, USER_NOT_FOUND_MESSAGE)
    # Lockout guard (T6, no password-reset flow exists in V0): an admin may not demote or
    # disable their own account.
    if user_id == current_user.id and (
        (body.role is not None and body.role != UserRole.admin) or body.is_active is False
    ):
        raise HTTPException(409, CANNOT_DEMOTE_OR_DISABLE_SELF_MESSAGE)
    if body.department_ids is not None:
        _check_department_ids(session, body.department_ids)
    try:
        user = user_repo.update(
            session,
            user,
            display_name=body.display_name,
            role=body.role,
            is_active=body.is_active,
            department_ids=body.department_ids,
            title=body.title,
            primary_department_id=body.primary_department_id,
            primary_department_given="primary_department_id" in body.model_fields_set,
        )
    except user_repo.PrimaryDepartmentNotAMembershipError:
        raise HTTPException(422, PRIMARY_DEPARTMENT_NOT_A_MEMBERSHIP_MESSAGE) from None
    session.commit()
    return UserResponse.model_validate(user)
