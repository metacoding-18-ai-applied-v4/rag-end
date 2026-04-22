"""ParentDocumentRetriever -- 자식 청크로 검색하고 부모(원본) 문서를 반환합니다."""

from __future__ import annotations

from typing import Any

from ._retriever_utils import (
    cosine_similarity,
    build_parent_index,
    embed_child_chunks,
)


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
        # TODO: 자식 청크로 검색하고 부모 문서를 반환합니다.
        # 1. 자식 청크별 유사도 계산
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

        # 2. 중복 제거: 같은 부모는 한 번만
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
