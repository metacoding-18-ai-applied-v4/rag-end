"""Multi-Query -- 하나의 질문을 여러 관점으로 재작성하고 병합 검색합니다."""

from __future__ import annotations

from typing import Any

from ._rewriter_utils import (
    score_with_embedding,
    score_with_keyword,
    generate_queries_llm,
)


def generate_multi_queries(
    query: str,
    num_queries: int = 3,
) -> list[str]:
    """다양한 관점의 쿼리를 생성합니다.

    Returns:
        [원본 쿼리, 재표현1, 재표현2, ...] (원본 포함 num_queries+1개)
    """
    # TODO: LLM을 호출하고 결과를 줄 단위로 파싱합니다.
    # 1. LLM으로 재작성 질문 생성
    queries = generate_queries_llm(query, num_queries)
    return queries


def search_multi_query(
    queries: list[str],
    documents: list[dict],
    embeddings: Any | None = None,
    top_k: int = 3,
) -> list[dict]:
    """다중 쿼리로 검색하고 결과를 병합합니다."""
    # TODO: 다중 쿼리 각각으로 검색하고 최고 점수 기준으로 병합합니다.
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
