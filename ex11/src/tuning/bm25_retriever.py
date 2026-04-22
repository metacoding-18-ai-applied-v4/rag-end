"""CH08 하이브리드 검색의 BM25 축. rank-bm25 라이브러리 기반 키워드 검색기.

ex11은 이 클래스를 그대로 import해 ChromaDB 벡터 검색과 앙상블한다.
"""

from __future__ import annotations

import sys


class BM25Retriever:
    """BM25 키워드 기반 검색기 (CH08 step3_hybrid_search 원본)."""

    def __init__(self, documents: list[str], metadatas: list[dict] | None = None) -> None:
        self.documents = documents
        self.metadatas = metadatas or [{} for _ in documents]
        self.bm25 = self._build_index(documents)

    def _build_index(self, documents: list[str]):
        try:
            from rank_bm25 import BM25Okapi

            tokenized_docs = [doc.lower().split() for doc in documents]
            return BM25Okapi(tokenized_docs)
        except ImportError:
            print("[bm25] rank-bm25 미설치. pip install rank-bm25", file=sys.stderr)
            sys.exit(1)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)

        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        results: list[dict] = []
        for idx, score in ranked:
            results.append({
                "content": self.documents[idx],
                "score": float(score),
                "metadata": self.metadatas[idx],
                "retriever_type": "bm25",
            })
        return results
