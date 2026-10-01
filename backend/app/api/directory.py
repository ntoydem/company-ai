"""`GET /api/directory?q=&department=` (B-05, Aşama C): the company people list every
signed-in user may read — `/api/users` stays admin-only. Returns five fields and nothing
else (no username, role, activity flag, hash). Unknown department → empty list, never 404."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.user import User
from app.repositories import user_repo
from app.schemas.directory import DirectoryPerson

router = APIRouter(prefix="/api/directory", tags=["directory"])


@router.get("", response_model=list[DirectoryPerson])
def list_directory(
    session: Annotated[Session, Depends(get_session)],
    _user: Annotated[User, Depends(get_current_user)],
    q: Annotated[str | None, Query(max_length=128)] = None,
    department: Annotated[str | None, Query(max_length=64)] = None,
) -> list[DirectoryPerson]:
    people = user_repo.search_directory(session, q=q, department_slug=department)
    return [
        DirectoryPerson(
            id=person.id,
            display_name=person.display_name,
            title=person.title,
            department_slug=person.primary_department_slug,
            department_name=(person.primary_department.name if person.primary_department else None),
        )
        for person in people
    ]
