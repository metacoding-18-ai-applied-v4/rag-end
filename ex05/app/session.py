"""ex05 — 세션 관리 모듈."""

import uuid

from fastapi import Request
from fastapi.responses import JSONResponse


SESSION_COOKIE_NAME = "rag_session_id"


def get_session_id(request):
    """요청에서 세션 ID를 읽어 반환한다."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)

    if not session_id:
        session_id = str(uuid.uuid4())

    return session_id


def set_session_cookie(response, session_id):
    """응답 객체에 세션 쿠키를 설정한다."""
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,       # JavaScript 접근 차단 (XSS 방지)
        samesite="lax",      # CSRF 방지
        max_age=3600,        # 1시간
    )

    return response


def generate_session_id():
    """새로운 UUID v4 기반 세션 ID를 생성하여 반환한다."""
    return str(uuid.uuid4())
