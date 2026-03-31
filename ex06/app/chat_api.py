"""ex06 — 채팅 API 라우터."""

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
    """IntegratedAgent 싱글턴을 반환한다."""
    global _agent_instance
    if _agent_instance is None:
        # sys.path에 src/ 추가
        src_path = os.path.join(_BASE_DIR, "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        from src.agent import IntegratedAgent
        _agent_instance = IntegratedAgent()
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


@router.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(body: ChatRequest):
    """사용자 질문을 처리하고 답변을 반환한다."""
    src_path = os.path.join(_BASE_DIR, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    if body.use_agent:
        # ① 통합 에이전트 모드
        try:
            agent = _get_agent()  # ①
            result = agent.run(body.query)
            return ChatResponse(
                query=body.query,
                answer=result["answer"],
                query_type=result.get("query_type", "unstructured"),
                mode="agent",
                structured_data=result.get("structured_data", {}),
                unstructured_data=result.get("unstructured_data", []),
                steps=result.get("steps", []),
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
            from src.mcp_tools import search_documents
            from src.router import QueryRouter

            query_router = _get_router()  # ②
            query_type = query_router.classify_query(body.query)

            search_result = search_documents.invoke({"query": body.query, "k": 3})  # ③
            docs = search_result.get("results", []) if isinstance(search_result, dict) else []

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
