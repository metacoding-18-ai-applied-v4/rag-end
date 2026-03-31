"""
FastAPI 애플리케이션 진입점.

사내 AI 비서 ex02 -- 사내 CRUD 시스템 + Admin UI를 시작합니다.
  - /admin/*   : Jinja2 Admin UI (views.py)
  - /api/*     : REST JSON API (api.py)
  - /          : /admin/dashboard 로 리다이렉트

실행 명령:
    python run.py
"""

import os
import sys

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

# ------------------------------------------------------------------
# [INPUT] 환경 변수 및 필수 설정 확인
# ------------------------------------------------------------------
load_dotenv()

# ------------------------------------------------------------------
# [PROCESS] FastAPI 앱 생성 및 라우터 등록
# ------------------------------------------------------------------
app = FastAPI(
    title="사내 AI 비서 — CRUD 시스템",
    description="ex02 FastAPI + PostgreSQL CRUD 시스템",
    version="1.0.0",
)

# 정적 파일 마운트 (CSS 등)
app.mount("/static", StaticFiles(directory="static"), name="static")   # ①

# 라우터 등록 (순환 임포트 방지를 위해 여기서 임포트)
from app import views, api                                              # ②
app.include_router(views.router)                                        # ③ Admin UI
app.include_router(api.router)                                          # ④ REST API


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    """루트 경로 접근 시 Admin 대시보드로 리다이렉트합니다.

    Returns:
        대시보드로의 리다이렉트 응답
    """
    return RedirectResponse(url="/admin/dashboard")                     # ⑤


# ------------------------------------------------------------------
# [OUTPUT] 서버 시작 (직접 실행 시)
# ------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("FASTAPI_HOST", "0.0.0.0")
    port = int(os.getenv("FASTAPI_PORT", "8000"))

    print("=" * 55)
    print("  사내 AI 비서 — CRUD 시스템 (ex02)")
    print(f"  Admin UI : http://localhost:{port}/admin/dashboard")
    print(f"  API 문서 : http://localhost:{port}/docs")
    print("=" * 55)

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
    )
