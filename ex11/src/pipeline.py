"""ex11 — 커넥트HR 에이전트 RAG 파이프라인 (Application Layer).

레이어드 아키텍처로 정리한 D 조합 파이프라인.

  Application Layer : `RagPipeline` (이 파일) — 도메인 객체를 조립·순서 실행
  Domain Layer      : `src.tuning.*`          — QueryExpander·EnsembleRetriever·
                                                 CrossEncoderReranker·
                                                 ParentDocumentRetriever
  Infrastructure    : `src.tools.search_documents` — 자식·부모 분리 인덱싱,
                       ChromaDB · rank-bm25 · sentence-transformers 런타임 의존

인덱싱 시점에는 `tuning.hybrid_parser`가 스캔본까지 텍스트로 꺼내 페이지
단위 부모 문서와 짧은 자식 청크를 동시에 만들어 둔다. 여기서는 질의
단계만 조립한다.

질의 흐름:
  1. QueryExpander.expand(q)                     — 약어 사전으로 확장
  2. EnsembleRetriever.search(q, k)              — BM25 + ChromaDB(Vector) 자식 검색
  3. CrossEncoderReranker.rerank(q, docs)        — 딥러닝 모델 재정렬
  4. ParentDocumentRetriever.resolve(docs, k)    — 자식 → 부모 복원 (중복 제거)
  5. top-k 반환
"""

from __future__ import annotations

from typing import List

from .tuning import (
    CrossEncoderReranker,
    EnsembleRetriever,
    ParentDocumentRetriever,
    QueryExpander,
)


class RagPipeline:
    """도메인 객체를 조립한 질의 파이프라인."""

    def __init__(
        self,
        expander: QueryExpander | None = None,
        retriever: EnsembleRetriever | None = None,
        reranker: CrossEncoderReranker | None = None,
        parent_retriever: ParentDocumentRetriever | None = None,
        alpha: float = 0.5,
    ) -> None:
        # 생성자 주입 — 외부 테스트·교체가 쉽다
        self.expander = expander or QueryExpander()
        self.reranker = reranker or CrossEncoderReranker()

        if retriever is not None and parent_retriever is not None:
            self.retriever = retriever
            self.parent_retriever = parent_retriever
            return

        from .tools.search_documents import _get_store

        collection, parent_docs = _get_store()
        self.retriever = (
            EnsembleRetriever(collection, alpha=alpha) if collection is not None else None
        )
        self.parent_retriever = (
            ParentDocumentRetriever(child_collection=collection, parent_docs=parent_docs)
            if collection is not None and parent_docs
            else None
        )

    def run(self, query: str, k: int = 3) -> List[dict]:
        if self.retriever is None or self.parent_retriever is None:
            return []
        # 1) 약어 확장
        expanded = self.expander.expand(query)
        # 2) 자식 청크 하이브리드 검색
        retrieved = self.retriever.search(expanded, k=k)
        if not retrieved:
            return []
        # 3) Cross-Encoder 리랭크 (자식 단위)
        reranked = self.reranker.rerank(expanded, retrieved, top_k=k * 2)
        # 4) 자식 → 부모 페이지 복원 (중복 제거)
        parents = self.parent_retriever.resolve(reranked, top_k=k)
        # 5) 상위 k
        return parents[:k]


# ---------------------------------------------------------------------------
# 싱글톤 진입점 — 외부에서 run_pipeline(query, k) 한 줄이면 된다
# ---------------------------------------------------------------------------

_PIPELINE: RagPipeline | None = None


def run_pipeline(query: str, k: int = 3) -> List[dict]:
    """싱글톤 RagPipeline을 통해 질의를 실행한다."""
    global _PIPELINE
    if _PIPELINE is None:
        _PIPELINE = RagPipeline()
    return _PIPELINE.run(query, k=k)
