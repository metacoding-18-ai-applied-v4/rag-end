"""Query Rewrite 보조 유틸리티 -- 헬퍼 함수, LLM 호출, 점수 계산 등 완성 코드."""

from __future__ import annotations

import math
import os
from typing import Any

from rich.console import Console

console = Console()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")


# ---------------------------------------------------------------------------
# 코사인 유사도
# ---------------------------------------------------------------------------

def cosine_similarity(a: list[float], b: list[float]) -> float:
    """두 벡터의 코사인 유사도를 계산합니다."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# Ollama LLM 호출
# ---------------------------------------------------------------------------

def call_ollama(prompt: str) -> str | None:
    """Ollama API를 httpx로 호출합니다. 실패 시 None 반환."""
    try:
        import httpx

        resp = httpx.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except Exception as exc:
        console.print(f"[yellow]Ollama 호출 실패: {exc}[/yellow]")
        return None


# ---------------------------------------------------------------------------
# HyDE 가상 문서 생성
# ---------------------------------------------------------------------------

def generate_hypothetical_doc_llm(query: str) -> str | None:
    """LLM으로 가상 답변 문서를 생성합니다."""
    prompt = (
        "다음 질문에 대한 가상의 사내 규정 문서 발췌문을 생성하십시오.\n"
        "실제 존재하는 문서처럼 구체적인 내용으로 3-5문장 작성하십시오.\n\n"
        f"질문: {query}\n\n"
        "사내 규정 발췌문:"
    )
    return call_ollama(prompt)


def generate_hypothetical_doc_rule(query: str) -> str:
    """규칙 기반으로 가상 문서를 생성합니다 (LLM fallback)."""
    templates = {
        "연차": (
            "연차유급휴가 규정에 따르면, 직원은 1년 이상 근속 시 15일의 유급휴가를 받습니다. "
            "신청은 3일 전까지 서면으로 하며 팀장 승인이 필요합니다."
        ),
        "재택": (
            "재택근무 정책에 의거하여, 입사 6개월 이상 정규직 직원은 주 2회까지 "
            "재택근무를 신청할 수 있습니다. 팀장 사전 승인이 필요합니다."
        ),
        "출장": (
            "출장 규정에 따라, 출장비는 완료 후 5영업일 이내에 영수증과 함께 "
            "정산 신청해야 합니다. 숙박비 15만원, 식비 5만원이 한도입니다."
        ),
        "보안": (
            "정보보안 규정에 따르면, 비밀번호는 8자 이상으로 설정하고 90일마다 변경해야 합니다. "
            "보안 위반 시 징계 조치가 가능합니다."
        ),
        "평가": (
            "성과 평가 지침에 따르면, 평가는 상하반기 각 1회 실시하며 "
            "목표달성도 60%, 역량평가 30%, 동료평가 10%로 구성됩니다."
        ),
    }

    query_lower = query.lower()
    for keyword, template in templates.items():
        if keyword in query_lower:
            return template

    return f"{query}에 관한 사내 규정은 인사팀 담당자에게 문의하거나 사내 규정집을 참조하십시오."


# ---------------------------------------------------------------------------
# 점수 계산 / 검색 헬퍼
# ---------------------------------------------------------------------------

def score_with_embedding(
    text: str,
    documents: list[dict],
    embeddings: Any,
) -> list[tuple[float, dict]]:
    """임베딩 기반으로 텍스트와 문서들의 유사도를 계산합니다."""
    text_vec = embeddings.embed_query(text)
    doc_vecs = embeddings.embed_documents([d["content"] for d in documents])
    return [
        (cosine_similarity(text_vec, dv), doc)
        for dv, doc in zip(doc_vecs, documents)
    ]


def score_with_keyword(
    text: str,
    documents: list[dict],
) -> list[tuple[float, dict]]:
    """키워드 매칭으로 텍스트와 문서들의 유사도를 계산합니다."""
    words = set(text.lower().split())
    scored: list[tuple[float, dict]] = []
    for doc in documents:
        dw = set(doc["content"].lower().split())
        s = len(words & dw) / len(words) if words else 0.0
        scored.append((s, doc))
    return scored


def to_search_results(
    scored: list[tuple[float, dict]],
    top_k: int = 3,
) -> list[dict]:
    """점수 리스트를 정렬하여 상위 top_k개 결과 딕셔너리로 변환합니다."""
    scored_sorted = sorted(scored, key=lambda x: x[0], reverse=True)
    return [
        {
            "content": doc["content"],
            "source": doc.get("source", ""),
            "score": round(score, 4),
        }
        for score, doc in scored_sorted[:top_k]
    ]


# ---------------------------------------------------------------------------
# Multi-Query LLM 생성
# ---------------------------------------------------------------------------

def generate_queries_llm(query: str, num_queries: int = 3) -> list[str] | None:
    """LLM으로 다양한 관점의 쿼리를 생성합니다. 실패 시 None 반환."""
    prompt = (
        f"다음 질문을 {num_queries}가지 다른 방식으로 재표현하십시오.\n"
        "각 질문은 같은 정보를 구하지만 다른 표현 방식을 사용해야 합니다.\n"
        "번호 없이 각 질문을 한 줄씩 출력하십시오.\n\n"
        f"원본 질문: {query}\n\n"
        "재표현된 질문들:"
    )

    llm_result = call_ollama(prompt)
    if llm_result:
        lines = [
            line.strip()
            for line in llm_result.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]
        return [query] + lines[:num_queries]

    return None


def generate_queries_rule(query: str, num_queries: int = 3) -> list[str]:
    """규칙 기반으로 다양한 쿼리를 생성합니다 (LLM fallback)."""
    console.print("[dim]  (규칙 기반 Multi-Query fallback 사용)[/dim]")
    return [
        query,
        f"{query}에 대한 규정이 있습니까?",
        f"{query} 관련 정책 안내",
        f"{query} 절차 및 방법",
    ][:num_queries + 1]
