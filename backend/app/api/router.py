from fastapi import APIRouter

from app.api import ask, ask_page, audit_log, auth, departments, documents, excel, health, projects

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(departments.router)
router.include_router(projects.router)
router.include_router(documents.router)
router.include_router(ask.router)
router.include_router(ask_page.router)
router.include_router(audit_log.router)
router.include_router(excel.router)
