"""HyDE (Hypothetical Document Embeddings) -- 가상 문서 vs 직접 검색 비교."""

from __future__ import annotations

from typing import Any

from rich.console import Console

from ._rewriter_utils import (
    generate_hypothetical_doc_llm,
    score_with_embedding,
    score_with_keyword,
    to_search_results,
)

console = Console()


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
    # TODO: 가상 답변으로 검색한 결과와 직접 검색 결과를 비교합니다.
    # 1. LLM에 가상 답변 생성 요청
    hypo_doc = generate_hypothetical_doc_llm(query)

    # 2. 직접 검색과 HyDE 검색 점수 계산
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
