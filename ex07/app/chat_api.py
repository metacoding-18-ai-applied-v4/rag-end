"""채팅 API 라우터."""

import sys
import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 1. 라우터 및 템플릿 설정
# ---------------------------------------------------------------------------

router = APIRouter()

# 템플릿 경로 (app/ 기준으로 ../templates/)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(_BASE_DIR, "templates"))


# ---------------------------------------------------------------------------
# 2. 요청/응답 모델
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """채팅 요청 모델."""

    query: str = Field(..., description="사용자 질문 문자열")
    use_agent: bool = Field(default=True, description="통합 에이전트 사용 여부")


# route 값 → 프론트엔드 query_type 역매핑
_ROUTE_TO_TYPE = {
    "db": "structured",
    "rag": "unstructured",
    "agent": "hybrid",
    "agent_fallback": "hybrid",
}


class ChatResponse(BaseModel):
    """채팅 응답 모델."""

    query: str = Field(..., description="원본 질문")
    answer: str = Field(..., description="최종 답변")
    query_type: str = Field(default="unstructured", description="질문 유형: structured|unstructured|hybrid")
    mode: str = Field(default="agent", description="처리 모드: agent|rag")
    structured_data: dict = Field(default_factory=dict, description="DB 조회 결과")
    unstructured_data: list = Field(default_factory=list, description="문서 검색 결과")
    steps: list = Field(default_factory=list, description="에이전트 중간 단계")


# ---------------------------------------------------------------------------
# 3. 싱글턴 관리
# ---------------------------------------------------------------------------

_agent_instance = None
_router_instance = None


def _get_agent():
    """ConnectHRAgent 싱글턴을 반환한다."""
    global _agent_instance
    if _agent_instance is None:
        # sys.path에 src/ 추가
        src_path = os.path.join(_BASE_DIR, "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        from src.agent_config import get_agent
        _agent_instance = get_agent()
    return _agent_instance


def _get_router():
    """QueryRouter 싱글턴을 반환한다."""
    global _router_instance
    if _router_instance is None:
        src_path = os.path.join(_BASE_DIR, "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        from src.router import QueryRouter
        _router_instance = QueryRouter()
    return _router_instance


# ---------------------------------------------------------------------------
# 4. 엔드포인트 정의
# ---------------------------------------------------------------------------

@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """채팅 UI 페이지를 반환한다."""
    return templates.TemplateResponse("chat.html", {"request": request})


@router.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    """상태 확인 페이지를 반환한다."""
    return templates.TemplateResponse("stats.html", {"request": request})


@router.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(body: ChatRequest):
    """사용자 질문을 처리하고 답변을 반환한다."""
    src_path = os.path.join(_BASE_DIR, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    if body.use_agent:
        # ① 통합 에이전트 모드 (캐시 연동)
        try:
            agent = _get_agent()  # ①
            result = agent.run(body.query)

            # intermediate_steps에서 근거 데이터 추출
            structured_data = {}
            unstructured_data = []
            for step in result.get("intermediate_steps", []):
                if isinstance(step, (list, tuple)) and len(step) >= 2:
                    action, observation = step[0], step[1]
                    tool_name = getattr(action, "tool", "")
                    if tool_name in ("get_leave_balance", "list_employees", "get_sales_sum"):
                        structured_data[tool_name] = observation
                    elif tool_name == "search_documents" and isinstance(observation, list):
                        unstructured_data.extend(observation)

            return ChatResponse(
                query=body.query,
                answer=result.get("output", "답변을 생성하지 못했습니다."),
                query_type=_ROUTE_TO_TYPE.get(result.get("route", ""), "unstructured"),
                mode="agent",
                structured_data=structured_data,
                unstructured_data=unstructured_data,
                steps=result.get("intermediate_steps", []),
            )
        except Exception as e:
            return ChatResponse(
                query=body.query,
                answer=f"에이전트 처리 중 오류가 발생했습니다: {e}",
                mode="agent",
            )
    else:
        # ② 단순 RAG 모드 (문서 검색만)
        try:
            from src.tools.search_documents import search_documents
            from src.router import QueryRouter

            query_router = _get_router()  # ②
            query_type = query_router.classify_query(body.query)

            search_result = search_documents.invoke({"query": body.query})  # ③
            docs = search_result if isinstance(search_result, list) else []

            # 간단한 컨텍스트 조합 응답
            if docs:
                context = "\n\n".join(d["content"] for d in docs)
                answer = f"관련 문서에서 찾은 내용:\n\n{context}"
            else:
                answer = "관련 문서를 찾지 못했습니다."

            return ChatResponse(
                query=body.query,
                answer=answer,
                query_type=query_type,
                mode="rag",
                unstructured_data=docs,
            )
        except Exception as e:
            return ChatResponse(
                query=body.query,
                answer=f"RAG 검색 중 오류가 발생했습니다: {e}",
                mode="rag",
            )


@router.get("/api/stats")
async def stats_endpoint():
    """캐시 적중률과 토큰 사용량 통계를 반환한다."""
    from src.cache import response_cache
    from src.monitoring import token_tracker

    return {
        "response_cache": response_cache.stats(),
        "token_tracker": token_tracker.summary(),
    }


@router.post("/api/cache/clear")
async def cache_clear_endpoint():
    """응답 캐시를 전체 초기화한다."""
    from src.cache import response_cache

    before = len(response_cache._store)
    response_cache._store.clear()
    response_cache._hits = 0
    response_cache._misses = 0
    return {"cleared": before, "message": f"캐시 {before}건 초기화 완료"}
