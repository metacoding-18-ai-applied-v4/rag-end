"""SelfQueryRetriever -- 쿼리에서 메타데이터 필터를 자동 추출하여 필터링 검색합니다."""

from __future__ import annotations

from typing import Any

from ._retriever_utils import (
    extract_topic_filter,
    apply_metadata_filter,
    score_documents_by_embedding,
    score_documents_by_keyword,
)


class SelfQueryRetriever:
    """쿼리에서 메타데이터 필터를 자동 추출하여 필터링 검색."""

    def __init__(
        self,
        documents: list[dict],
        topic_keywords: dict[str, list[str]] | None = None,
        embeddings: Any | None = None,
    ) -> None:
        self.documents = documents
        self.topic_keywords = topic_keywords or {}
        self.embeddings = embeddings

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """메타데이터 필터를 자동 추출한 뒤 필터링 검색합니다."""
        filters = extract_topic_filter(query, self.topic_keywords)
        filtered = apply_metadata_filter(self.documents, filters)

        # 점수 계산
        if self.embeddings is not None:
            scored = score_documents_by_embedding(query, filtered, self.embeddings)
        else:
            scored = score_documents_by_keyword(query, filtered)

        scored.sort(key=lambda x: x[0], reverse=True)

        results: list[dict] = []
        for score, doc in scored[:top_k]:
            results.append({
                "content": doc["content"],
                "score": round(score, 4),
                "metadata": doc.get("metadata", {}),
                "applied_filter": filters,
                "retriever_type": "self_query",
            })

        return results
