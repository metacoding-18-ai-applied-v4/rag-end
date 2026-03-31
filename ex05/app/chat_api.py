"""ex05 — 채팅 API 라우터 모듈."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.session import get_session_id, set_session_cookie
from src.session_manager import get_conversation_manager
from src.rag_chain import get_rag_chain
from src.response_parser import build_response

class ChatRequest(BaseModel):
    """채팅 API 요청 스키마."""

    question: str = Field(..., min_length=1, max_length=2000, description="사용자 질문")
    session_id: str | None = Field(None, description="세션 ID (없으면 자동 생성)")


class SourceItem(BaseModel):
    """출처 항목 스키마."""

    doc: str = Field(..., description="문서명")
    page: int = Field(..., description="페이지 번호")
    snippet: str = Field(..., description="관련 내용 앞부분")


class ChatResponse(BaseModel):
    """채팅 API 응답 스키마."""

    answer: str = Field(..., description="AI 답변")
    sources: list[SourceItem] = Field(default_factory=list, description="참조 출처 목록")
    session_id: str = Field(..., description="세션 ID")


router = APIRouter(prefix="/api", tags=["chat"])

@router.post("/chat")
async def chat_endpoint(body: ChatRequest, request: Request):
    """사용자 질문을 받아 RAG 체인으로 답변을 생성하고 반환한다."""
    # 세션 ID: 요청 본문 > 쿠키 > 신규 생성 순으로 결정
    session_id = body.session_id or get_session_id(request)
    question = body.question.strip()

    if not question:
        return JSONResponse(
            status_code=400,
            content={"error": "질문이 비어 있습니다. 내용을 입력해 주세요."},
        )

    try:
        # 대화 매니저에서 이전 대화 히스토리 조회
        conv_manager = get_conversation_manager()
        history_text = conv_manager.get_history_text(session_id)

        # RAG 체인과 Retriever 로드
        chain, retriever = get_rag_chain()

        # Retriever로 관련 문서 검색 (출처 표시에 사용)
        docs = retriever.invoke(question)

        # LCEL 체인 실행: {"question": ..., "history": ...} 형식으로 입력
        # 체인 내부에서 question → 검색 → 포맷 → 프롬프트 → LLM 순서로 처리
        raw_answer = chain.invoke(
            {
                "question": question,   # ① 검색 및 프롬프트에 사용
                "history": history_text,  # ② 이전 대화 맥락 주입
            }
        )

        # 응답 구조 생성 (answer 정제 + sources 추출)
        response_data = build_response(raw_answer=raw_answer, docs=docs)
        response_data["session_id"] = session_id

        # 세션 히스토리에 이번 대화 저장
        conv_manager.save_turn(
            session_id=session_id,
            question=question,
            answer=response_data["answer"],
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": (
                    f"답변 생성 중 오류가 발생했습니다: {str(e)}\n"
                    "LLM 서버(Ollama)가 실행 중인지 확인해 주세요. "
                    "OpenAI를 사용하려면 .env에서 LLM_PROVIDER=openai로 변경하세요."
                ),
                "session_id": session_id,
            },
        )

    json_response = JSONResponse(content=response_data)
    set_session_cookie(json_response, session_id)
    return json_response
@router.delete("/chat/session")
async def clear_session_endpoint(request: Request):
    """현재 세션의 대화 히스토리를 초기화한다."""
    session_id = get_session_id(request)

    conv_manager = get_conversation_manager()
    conv_manager.clear_session(session_id)

    response = JSONResponse(
        content={
            "message": "대화 히스토리가 초기화되었습니다.",
            "session_id": session_id,
        }
    )
    set_session_cookie(response, session_id)
    return response
