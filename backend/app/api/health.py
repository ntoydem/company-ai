from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy import Engine

from app import __version__
from app.core.db import database_reachable, get_engine
from app.schemas.health import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health(engine: Annotated[Engine, Depends(get_engine)], response: Response) -> HealthResponse:
    db_ok = database_reachable(engine)
    if not db_ok:
        response.status_code = 503
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        version=__version__,
        database="ok" if db_ok else "unavailable",
    )
