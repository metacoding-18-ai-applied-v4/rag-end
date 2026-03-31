"""ex05 — RAG 응답 파서 모듈."""

import re

from langchain.schema import Document

def parse_answer_text(raw_answer):
    """LLM 원문 응답에서 <think>...</think> 태그를 제거하고 답변 텍스트만 반환한다."""
    text = raw_answer

    # DeepSeek R1의 <think> 추론 토큰 제거
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = text.strip()

    # 빈 문자열이면 기본 메시지 반환
    if not text:
        text = "답변을 생성하지 못했습니다. 다시 시도해 주세요."

    return text

def parse_sources_from_docs(docs):
    """검색된 Document 목록에서 출처 정보를 추출하여 반환한다."""
    sources = []

    seen_sources = set()
    for doc in docs:
        source = doc.metadata.get("source", "알 수 없는 문서")
        page = doc.metadata.get("page", 0)
        # 동일 출처 중복 제거
        source_key = f"{source}::{page}"
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)

        snippet = doc.page_content[:120].strip()
        if len(doc.page_content) > 120:
            snippet += "..."

        sources.append(
            {
                "doc": source,
                "page": int(page) if page else 0,
                "snippet": snippet,
            }
        )

    return sources




def build_response(raw_answer, docs):
    """LLM 원문 응답과 검색 문서로부터 최종 API 응답 딕셔너리를 구성한다."""
    answer = parse_answer_text(raw_answer)
    sources = parse_sources_from_docs(docs)

    return {
        "answer": answer,
        "sources": sources,
    }
