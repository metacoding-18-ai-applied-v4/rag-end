"""ex05 — LCEL 기반 RAG 체인 모듈."""

from operator import itemgetter

from dotenv import load_dotenv
from langchain.schema import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.llm_factory import build_llm
from src.vectorstore import build_retriever

load_dotenv()

# =============================================================
# 출처 강제 + "모르면 확인되지 않음" RAG 프롬프트 템플릿
# =============================================================
RAG_SYSTEM_PROMPT = """당신은 메타코딩 사내 문서 Q&A 비서입니다.
아래에 제공된 문서(Context)만 사용하여 질문에 답변하십시오.

규칙:
1. 반드시 제공된 문서에서만 근거를 찾아 답변하시오.
2. 문서에서 답을 찾을 수 없으면 "해당 내용은 제공된 문서에서 확인되지 않습니다."라고 답하시오.
3. 답변 마지막에 근거 문서명을 반드시 명시하시오. 형식: [출처: 문서명]
4. 추측이나 외부 지식을 사용하지 마시오.

Context (제공된 문서):
{context}

이전 대화:
{history}
"""

RAG_HUMAN_PROMPT = "질문: {question}"


def _format_docs(docs):
    """검색된 Document 목록을 프롬프트에 삽입할 텍스트 형식으로 변환한다."""
    parts = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "알 수 없음")
        page = doc.metadata.get("page", "-")
        parts.append(f"[문서 {i}] 출처: {source} (p.{page})\n{doc.page_content}")
    return "\n\n".join(parts)


def build_rag_chain():
    """LCEL 파이프 연산자(|)로 RAG 체인과 Retriever를 조립하여 반환한다."""
    llm = build_llm()                # ① LLM 인스턴스 생성
    retriever = build_retriever()    # ② Retriever 생성 (ChromaDB)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", RAG_SYSTEM_PROMPT),
            ("human", RAG_HUMAN_PROMPT),
        ]
    )

    # LCEL 파이프: 입력 dict에서 각 키를 꺼내 병렬 처리 후 프롬프트로 합침
    chain = (
        {
            "context": itemgetter("question") | retriever | _format_docs,
            "history": itemgetter("history"),
            "question": itemgetter("question"),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, retriever


# 싱글턴 캐시 (앱 시작 시 1회만 초기화)
_rag_chain_cache = None
_retriever_cache = None


def get_rag_chain():
    """RAG 체인과 Retriever 싱글턴 인스턴스를 반환한다."""
    global _rag_chain_cache, _retriever_cache
    if _rag_chain_cache is None:
        _rag_chain_cache, _retriever_cache = build_rag_chain()
    return _rag_chain_cache, _retriever_cache
