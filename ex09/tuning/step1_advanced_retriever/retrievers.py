"""step1 Retriever 구현 -- ParentDoc / SelfQuery / ContextualCompression.

학습 목표:
  - ParentDocumentRetriever: 자식 청크로 검색 -> 부모 문서 반환
  - SelfQueryRetriever: 쿼리에서 메타데이터 필터 추출 -> 필터링 검색
  - ContextualCompressionRetriever: 검색 후 관련 문장만 압축 반환
"""

from __future__ import annotations

from typing import Any

from ._retriever_utils import (
    cosine_similarity,
    compress,
    score_documents_by_embedding,
    score_documents_by_keyword,
    build_parent_index,
    embed_child_chunks,
    extract_topic_filter,
    apply_metadata_filter,
)


# ---------------------------------------------------------------------------
# ParentDocumentRetriever
# ---------------------------------------------------------------------------

class ParentDocumentRetriever:
    """자식 청크로 검색 -> 부모(원본) 문서 반환."""

    def __init__(
        self,
        parent_docs: list[dict],
        child_chunks: list[dict],
        embeddings: Any | None = None,
    ) -> None:
        self.parent_docs = build_parent_index(parent_docs)
        self.child_chunks = child_chunks
        self.embeddings = embeddings
        self._child_vectors: list[list[float]] | None = None

        if self.embeddings is not None:
            self._child_vectors = embed_child_chunks(child_chunks, embeddings)

    def search(self, query: str, top_k: int = 2) -> list[dict]:
        """자식 청크에서 유사도가 높은 것을 찾고, 해당 부모 문서를 반환합니다."""
        scored_chunks: list[tuple[float, dict]] = []

        if self.embeddings is not None and self._child_vectors is not None:
            query_vec = self.embeddings.embed_query(query)
            for vec, chunk in zip(self._child_vectors, self.child_chunks):
                score = cosine_similarity(query_vec, vec)
                scored_chunks.append((score, chunk))
        else:
            query_words = set(query.lower().split())
            for chunk in self.child_chunks:
                chunk_words = set(chunk["content"].lower().split())
                score = len(query_words & chunk_words) / len(query_words) if query_words else 0.0
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        seen_parents: set[str] = set()
        results: list[dict] = []

        for score, chunk in scored_chunks:
            parent_id = chunk["parent_id"]
            if parent_id not in seen_parents and len(results) < top_k:
                seen_parents.add(parent_id)
                parent_doc = self.parent_docs.get(parent_id)
                if parent_doc:
                    results.append({
                        "parent_title": parent_doc["title"],
                        "parent_content": parent_doc["content"],
                        "child_chunk": chunk["content"],
                        "metadata": parent_doc.get("metadata", {}),
                        "score": round(score, 4),
                        "retriever_type": "parent_document",
                    })

        return results


# ---------------------------------------------------------------------------
# SelfQueryRetriever
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# ContextualCompressionRetriever
# ---------------------------------------------------------------------------

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
        if self.embeddings is not None:
            scored = score_documents_by_embedding(query, self.documents, self.embeddings)
        else:
            scored = score_documents_by_keyword(query, self.documents)

        scored.sort(key=lambda x: x[0], reverse=True)

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
