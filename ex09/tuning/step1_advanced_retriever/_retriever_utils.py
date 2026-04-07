"""Retriever 보조 유틸리티 -- 헬퍼 함수, 초기화, 점수 계산 등 완성 코드."""

from __future__ import annotations

import math
from typing import Any


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
# 문서 압축 (ContextualCompression 핵심)
# ---------------------------------------------------------------------------

def compress(query: str, document: str) -> str:
    """문서에서 쿼리와 관련된 문장만 추출합니다."""
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
# 점수 계산 헬퍼
# ---------------------------------------------------------------------------

def score_documents_by_embedding(
    query: str,
    documents: list[dict],
    embeddings: Any,
    content_key: str = "content",
) -> list[tuple[float, dict]]:
    """임베딩 기반으로 문서 점수를 계산합니다."""
    query_vec = embeddings.embed_query(query)
    doc_vecs = embeddings.embed_documents([d[content_key] for d in documents])
    return [
        (cosine_similarity(query_vec, dv), doc)
        for dv, doc in zip(doc_vecs, documents)
    ]


def score_documents_by_keyword(
    query: str,
    documents: list[dict],
    content_key: str = "content",
) -> list[tuple[float, dict]]:
    """키워드 매칭으로 문서 점수를 계산합니다 (임베딩 없을 때 폴백)."""
    query_words = set(query.lower().split())
    scored: list[tuple[float, dict]] = []
    for doc in documents:
        content_words = set(doc[content_key].lower().split())
        score = len(query_words & content_words) / len(query_words) if query_words else 0.0
        scored.append((score, doc))
    return scored


# ---------------------------------------------------------------------------
# ParentDocumentRetriever 초기화 헬퍼
# ---------------------------------------------------------------------------

def build_parent_index(parent_docs: list[dict]) -> dict[str, dict]:
    """부모 문서 리스트를 id -> doc 딕셔너리로 변환합니다."""
    return {doc["id"]: doc for doc in parent_docs}


def embed_child_chunks(
    child_chunks: list[dict],
    embeddings: Any,
) -> list[list[float]]:
    """자식 청크들의 임베딩 벡터를 미리 계산합니다."""
    return embeddings.embed_documents([c["content"] for c in child_chunks])


# ---------------------------------------------------------------------------
# SelfQueryRetriever 필터 헬퍼
# ---------------------------------------------------------------------------

def extract_topic_filter(
    query: str,
    topic_keywords: dict[str, list[str]],
) -> dict[str, str]:
    """쿼리에서 토픽 키워드를 매칭하여 메타데이터 필터를 추출합니다."""
    filters: dict[str, str] = {}
    query_lower = query.lower()

    for topic, keywords in topic_keywords.items():
        if any(kw in query_lower for kw in keywords):
            filters["topic"] = topic
            break

    return filters


def apply_metadata_filter(
    documents: list[dict],
    filters: dict[str, str],
) -> list[dict]:
    """메타데이터 필터를 적용하여 문서를 걸러냅니다."""
    filtered = documents
    for key, value in filters.items():
        filtered = [
            doc for doc in filtered
            if doc.get("metadata", {}).get(key) == value
        ]
    return filtered
