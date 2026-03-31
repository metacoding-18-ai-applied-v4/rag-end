"""채팅 API 라우터 — ex10 에이전트 + RAG + PDF 캡처 이미지 근거."""

import os
import sys

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 1. 라우터 및 템플릿 설정
# ---------------------------------------------------------------------------

router = APIRouter()

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
    evidence_images: list = Field(default_factory=list, description="근거 PDF 캡처 이미지")


# ---------------------------------------------------------------------------
# 3. 싱글턴 관리
# ---------------------------------------------------------------------------

_agent_instance = None
_router_instance = None
_vectorstore = None


def _get_agent():
    """ConnectHRAgent 싱글턴을 반환한다."""
    global _agent_instance
    if _agent_instance is None:
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


def _get_vectorstore():
    """ChromaDB 벡터스토어 싱글턴을 반환한다."""
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    try:
        import chromadb
        from chromadb.config import Settings

        db_path = os.path.join(_BASE_DIR, "data", "chroma_db")
        if not os.path.isdir(db_path):
            return None

        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False),
        )
        _vectorstore = client.get_or_create_collection("documents")
        return _vectorstore
    except Exception as e:
        print(f"[경고] ChromaDB 로드 실패: {e}")
        return None


def _dedupe_images(images):
    """URL 기준으로 중복 이미지를 제거한다."""
    seen = set()
    unique = []
    for img in images:
        url = img.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(img)
    return unique


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

    from src.evidence import resolve_image_url

    if body.use_agent:
        # ① 통합 에이전트 모드
        try:
            agent = _get_agent()
            result = agent.run(body.query)

            # intermediate_steps에서 근거 데이터 추출
            structured_data = {}
            unstructured_data = []
            evidence_images = []
            for step in result.get("intermediate_steps", []):
                if isinstance(step, (list, tuple)) and len(step) >= 2:
                    action, observation = step[0], step[1]
                    tool_name = getattr(action, "tool", "")
                    if tool_name in ("get_leave_balance", "list_employees", "get_sales_sum"):
                        structured_data[tool_name] = observation
                    elif tool_name == "search_documents" and isinstance(observation, list):
                        unstructured_data.extend(observation)
                        # 문서 검색 결과에서 캡처 이미지 추출
                        for doc in observation:
                            if isinstance(doc, dict):
                                image_path = doc.get("image_path", "")
                                if image_path:
                                    web_url = resolve_image_url(image_path)
                                    if web_url:
                                        evidence_images.append({
                                            "url": web_url,
                                            "source": doc.get("source", ""),
                                            "page": doc.get("page", ""),
                                        })

            return ChatResponse(
                query=body.query,
                answer=result.get("output", "답변을 생성하지 못했습니다."),
                query_type=_ROUTE_TO_TYPE.get(result.get("route", ""), "unstructured"),
                mode="agent",
                structured_data=structured_data,
                unstructured_data=unstructured_data,
                steps=result.get("intermediate_steps", []),
                evidence_images=_dedupe_images(evidence_images),
            )
        except Exception as e:
            return ChatResponse(
                query=body.query,
                answer=f"에이전트 처리 중 오류가 발생했습니다: {e}",
                mode="agent",
            )
    else:
        # ② RAG 모드 (문서 검색 + 캡처 이미지)
        collection = _get_vectorstore()

        if collection is None:
            # 벡터 DB 없으면 단순 RAG 시도
            try:
                from src.tools.search_documents import search_documents
                query_router = _get_router()
                query_type = query_router.classify_query(body.query)

                search_result = search_documents.invoke({"query": body.query})
                docs = search_result if isinstance(search_result, list) else []

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

        try:
            # ChromaDB 벡터 검색
            results = collection.query(
                query_texts=[body.query],
                n_results=5,
            )

            docs = []
            evidence_images = []

            if results and results["documents"]:
                for i, doc_text in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0
                    source = metadata.get("source", "사내 문서")

                    docs.append({
                        "content": doc_text[:300],
                        "source": source,
                        "score": round(1 - distance, 3),
                    })

                    # 캡처 이미지 경로가 메타데이터에 있으면 추가
                    image_path = metadata.get("image_path", "")
                    if image_path:
                        web_url = resolve_image_url(image_path)
                        if web_url:
                            evidence_images.append({
                                "url": web_url,
                                "source": source,
                                "page": metadata.get("page", ""),
                            })

            # 답변 생성
            if docs:
                context = "\n\n".join(d["content"] for d in docs)
                answer = f"관련 문서에서 찾은 내용:\n\n{context}"
            else:
                answer = "관련 문서를 찾지 못했습니다."

            return ChatResponse(
                query=body.query,
                answer=answer,
                mode="rag",
                unstructured_data=docs,
                evidence_images=_dedupe_images(evidence_images),
            )
        except Exception as e:
            return ChatResponse(
                query=body.query,
                answer=f"검색 중 오류가 발생했습니다: {e}",
                mode="rag",
            )


@router.get("/api/images")
async def list_images():
    """캡처된 이미지 목록을 반환한다."""
    src_path = os.path.join(_BASE_DIR, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    from src.evidence import list_captured_images
    return {"images": list_captured_images()}


@router.get("/api/stats")
async def stats_endpoint():
    """캐시 적중률과 토큰 사용량 통계를 반환한다."""
    src_path = os.path.join(_BASE_DIR, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    from src.cache import response_cache
    from src.monitoring import token_tracker

    return {
        "response_cache": response_cache.stats(),
        "token_tracker": token_tracker.summary(),
    }


@router.post("/api/cache/clear")
async def cache_clear_endpoint():
    """응답 캐시를 전체 초기화한다."""
    src_path = os.path.join(_BASE_DIR, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    from src.cache import response_cache

    before = len(response_cache._store)
    response_cache._store.clear()
    response_cache._hits = 0
    response_cache._misses = 0
    return {"cleared": before, "message": f"캐시 {before}건 초기화 완료"}
