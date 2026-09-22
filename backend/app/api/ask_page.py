"""Minimal single-file test page for `/api/ask` (Phase 0.3; the real frontend is Phase 3.3).
Served by the backend itself — no Caddy, no build step."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

ASK_PAGE_PATH = Path(__file__).resolve().parent.parent / "static" / "ask.html"

router = APIRouter(include_in_schema=False)


@router.get("/ask")
def ask_page() -> FileResponse:
    return FileResponse(ASK_PAGE_PATH, media_type="text/html; charset=utf-8")
