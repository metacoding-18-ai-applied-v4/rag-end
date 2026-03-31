"""FastAPI 애플리케이션 진입점."""

import os

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .admin_views import router as admin_router
from .chat_api import router as chat_router

# ---------------------------------------------------------------------------
# 1. FastAPI 앱 생성
# ---------------------------------------------------------------------------

app = FastAPI(
    title="ConnectHR ex07 - LangChain 연결",
    description="LangChain Agent + 캐시 + 모니터링 통합 데모",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# 2. 정적 파일 및 라우터 등록
# ---------------------------------------------------------------------------

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STATIC_DIR = os.path.join(_BASE_DIR, "static")

app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")  # ①
app.include_router(chat_router)  # ②
app.include_router(admin_router)  # ③ 관리자 대시보드


# ---------------------------------------------------------------------------
# 3. 루트 리다이렉트 및 헬스체크
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def root():
    """루트 경로를 채팅 페이지로 리다이렉트한다."""
    return RedirectResponse(url="/chat")


@app.get("/health")
async def health():
    """서버 상태를 반환한다."""
    return {"status": "ok", "version": "ex07", "title": "LangChain 운영 안정화"}
