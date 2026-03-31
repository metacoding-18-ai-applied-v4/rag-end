"""step1 Retriever 구현 -- ParentDoc / SelfQuery / ContextualCompression."""

from __future__ import annotations

import math
from typing import Any


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """두 벡터의 코사인 유사도를 계산합니다."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _compress(query: str, document: str) -> str:
    """문서에서 쿼리와 관련된 문장만 추출합니다 (ContextualCompression 핵심)."""
    query_words = set(query.lower().split())
    sentences = [s.strip() for s in document.replace("\n", ". ").split(".") if s.strip()]

    relevant: list[str] = []
    for sentence in sentences:
        sentence_words = set(sentence.lower().split())
        overlap = len(query_words & sentence_words)
        if overlap >= 1 and len(sentence) > 10:
            relevant.append(sentence)

    return ". ".join(relevant[:3]) if relevant else document[:100]


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
        self.parent_docs = {doc["id"]: doc for doc in parent_docs}
        self.child_chunks = child_chunks
        self.embeddings = embeddings
        self._child_vectors: list[list[float]] | None = None

        if self.embeddings is not None:
            self._child_vectors = self.embeddings.embed_documents(
                [c["content"] for c in self.child_chunks]
            )

    def search(self, query: str, top_k: int = 2) -> list[dict]:
        """검색을 수행합니다."""
        scored_chunks: list[tuple[float, dict]] = []

        if self.embeddings is not None and self._child_vectors is not None:
            query_vec = self.embeddings.embed_query(query)
            for vec, chunk in zip(self._child_vectors, self.child_chunks):
                score = _cosine_similarity(query_vec, vec)
                scored_chunks.append((score, chunk))
        else:
            # 키워드 폴백
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

    def extract_filter(self, query: str) -> dict[str, str]:
        """쿼리에서 메타데이터 필터를 추출합니다."""
        filters: dict[str, str] = {}
        query_lower = query.lower()

        for topic, keywords in self.topic_keywords.items():
            if any(kw in query_lower for kw in keywords):
                filters["topic"] = topic
                break

        return filters

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """메타데이터 자동 필터링으로 검색합니다."""
        filters = self.extract_filter(query)

        # 필터 적용
        filtered = self.documents
        for key, value in filters.items():
            filtered = [
                doc for doc in filtered
                if doc.get("metadata", {}).get(key) == value
            ]

        # 점수 계산
        scored: list[tuple[float, dict]] = []
        if self.embeddings is not None:
            query_vec = self.embeddings.embed_query(query)
            doc_vecs = self.embeddings.embed_documents([d["content"] for d in filtered])
            for vec, doc in zip(doc_vecs, filtered):
                score = _cosine_similarity(query_vec, vec)
                scored.append((score, doc))
        else:
            query_words = set(query.lower().split())
            for doc in filtered:
                content_words = set(doc["content"].lower().split())
                score = len(query_words & content_words) / len(query_words) if query_words else 0.0
                scored.append((score, doc))

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
# ContextualCompression (함수형)
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
        scored: list[tuple[float, dict]] = []

        if self.embeddings is not None:
            query_vec = self.embeddings.embed_query(query)
            doc_vecs = self.embeddings.embed_documents([d["content"] for d in self.documents])
            for vec, doc in zip(doc_vecs, self.documents):
                score = _cosine_similarity(query_vec, vec)
                scored.append((score, doc))
        else:
            query_words = set(query.lower().split())
            for doc in self.documents:
                content_words = set(doc["content"].lower().split())
                score = len(query_words & content_words) / len(query_words) if query_words else 0.0
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)

        results: list[dict] = []
        for score, doc in scored[:top_k]:
            original = doc["content"]
            compressed = _compress(query, original)
            results.append({
                "original_content": original,
                "compressed_content": compressed,
                "compression_ratio": round(len(compressed) / len(original), 2) if original else 0,
                "score": round(score, 4),
                "metadata": doc.get("metadata", {}),
                "retriever_type": "contextual_compression",
            })

        return results
