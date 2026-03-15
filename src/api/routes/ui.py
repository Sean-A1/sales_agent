"""UI 라우트 — 채팅 화면 서빙."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

STATIC_DIR = Path(__file__).resolve().parents[3] / "static"


@router.get("/", response_class=HTMLResponse)
async def index():
    """채팅 UI 메인 페이지."""
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)
