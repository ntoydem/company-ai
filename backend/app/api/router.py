from fastapi import APIRouter

from app.api import ask, ask_page, auth, documents, health

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(documents.router)
router.include_router(ask.router)
router.include_router(ask_page.router)
