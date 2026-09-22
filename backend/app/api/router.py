from fastapi import APIRouter

from app.api import documents, health

router = APIRouter()
router.include_router(health.router)
router.include_router(documents.router)
