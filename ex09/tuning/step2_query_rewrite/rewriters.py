"""step2 Query Rewrite 구현 -- 약어확장 / HyDE / Multi-Query.

학습 목표:
  - expand_abbreviations: 약어/동의어를 풀어써서 검색 품질 향상
  - compare_hyde_vs_direct: 가상 문서(HyDE) vs 직접 검색 비교
  - generate_multi_queries: 하나의 질문을 여러 관점으로 재작성
  - search_multi_query: 다중 쿼리로 검색하고 결과 병합
"""

from __future__ import annotations

from typing import Any

from rich.console import Console

from .data import ABBREVIATION_MAP, SYNONYM_MAP
from ._rewriter_utils import (
    cosine_similarity,
    generate_hypothetical_doc_llm,
    generate_hypothetical_doc_rule,
    score_with_embedding,
    score_with_keyword,
    to_search_results,
    generate_queries_llm,
    generate_queries_rule,
)

console = Console()


# ---------------------------------------------------------------------------
# 1) 약어/동의어 확장
# ---------------------------------------------------------------------------

def expand_abbreviations(query: str) -> dict:
    """쿼리의 약어와 동의어를 확장합니다.

    ABBREVIATION_MAP과 SYNONYM_MAP을 사용하여 쿼리 내 약어와 동의어를
    풀어씁니다.

    Returns:
        {"original": str, "expanded": str, "applied": list[str]}
    """
    expanded = query
    applied: list[str] = []

    # 약어 확장
    for abbrev, full_form in ABBREVIATION_MAP.items():
        if abbrev in expanded:
            expanded = expanded.replace(abbrev, full_form)
            applied.append(f"약어 '{abbrev}' -> '{full_form}'")

    # 동의어 확장
    for term, synonym in SYNONYM_MAP.items():
        if term in expanded and synonym not in expanded:
            expanded = expanded.replace(term, synonym)
            applied.append(f"동의어 '{term}' -> '{synonym}'")

    return {"original": query, "expanded": expanded, "applied": applied}


# ---------------------------------------------------------------------------
# 2) HyDE (Hypothetical Document Embeddings)
# ---------------------------------------------------------------------------

def compare_hyde_vs_direct(
    query: str,
    documents: list[dict],
    embeddings: Any | None = None,
) -> dict:
    """HyDE vs 직접 검색을 비교합니다.

    Returns:
        {
            "query": str,
            "hypothetical_doc": str,
            "direct_results": list[dict],
            "hyde_results": list[dict],
        }
    """
    # 가상 문서 생성
    hypo_doc = generate_hypothetical_doc_llm(query)
    if hypo_doc is None:
        hypo_doc = generate_hypothetical_doc_rule(query)
        console.print("[dim]  (규칙 기반 fallback 사용)[/dim]")

    # 직접 검색
    if embeddings is not None:
        direct_scored = score_with_embedding(query, documents, embeddings)
        hyde_scored = score_with_embedding(hypo_doc, documents, embeddings)
    else:
        direct_scored = score_with_keyword(query, documents)
        hyde_scored = score_with_keyword(hypo_doc, documents)

    return {
        "query": query,
        "hypothetical_doc": hypo_doc,
        "direct_results": to_search_results(direct_scored),
        "hyde_results": to_search_results(hyde_scored),
    }


# ---------------------------------------------------------------------------
# 3) Multi-Query
# ---------------------------------------------------------------------------

def generate_multi_queries(
    query: str,
    num_queries: int = 3,
) -> list[str]:
    """다양한 관점의 쿼리를 생성합니다.

    Returns:
        [원본 쿼리, 재표현1, 재표현2, ...] (원본 포함 num_queries+1개)
    """
    result = generate_queries_llm(query, num_queries)
    if result is not None:
        return result
    return generate_queries_rule(query, num_queries)


def search_multi_query(
    queries: list[str],
    documents: list[dict],
    embeddings: Any | None = None,
    top_k: int = 3,
) -> list[dict]:
    """다중 쿼리로 검색하고 결과를 병합합니다."""
    all_scored: dict[str, tuple[float, dict]] = {}

    for q in queries:
        if embeddings is not None:
            scored = score_with_embedding(q, documents, embeddings)
        else:
            scored = score_with_keyword(q, documents)

        for score, doc in scored:
            key = doc["content"][:50]
            if key not in all_scored or all_scored[key][0] < score:
                all_scored[key] = (score, doc)

    merged = sorted(all_scored.values(), key=lambda x: x[0], reverse=True)

    return [
        {
            "content": doc["content"],
            "source": doc.get("source", ""),
            "score": round(score, 4),
        }
        for score, doc in merged[:top_k]
    ]
