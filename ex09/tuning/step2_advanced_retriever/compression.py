"""ContextualCompressionRetriever -- 검색 후 관련 문장만 압축하여 반환합니다."""

from __future__ import annotations

from typing import Any

from ._retriever_utils import (
    compress,
    score_documents_by_embedding,
    score_documents_by_keyword,
)


class ContextualCompressionRetriever:
    """검색 후 관련 문장만 압축하여 반환."""

    def __init__(
        self,
        documents: list[dict],
        embeddings: Any | None = None,
    ) -> None:
        self.documents = documents
        self.embeddings = embeddings

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """검색 + 압축을 수행합니다."""
        # TODO: 검색 결과에서 질문과 관련된 문장만 압축합니다.
        # 1. 유사도 기준으로 문서 정렬
        if self.embeddings is not None:
            scored = score_documents_by_embedding(query, self.documents, self.embeddings)
        else:
            scored = score_documents_by_keyword(query, self.documents)

        scored.sort(key=lambda x: x[0], reverse=True)

        # 2. 핵심 문장만 추출 (최대 3문장)
        results: list[dict] = []
        for score, doc in scored[:top_k]:
            original = doc["content"]
            compressed = compress(query, original)
            results.append({
                "original_content": original,
                "compressed_content": compressed,
                "compression_ratio": round(len(compressed) / len(original), 2) if original else 0,
                "score": round(score, 4),
                "metadata": doc.get("metadata", {}),
                "retriever_type": "contextual_compression",
            })

        return results
