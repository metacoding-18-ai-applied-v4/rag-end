"""챕터 8 — BM25 + ChromaDB(Vector) 앙상블 검색 도메인 객체.

ChromaDB Collection을 주입받아 Vector 쪽을 맡기고, 같은 컬렉션에서
뽑은 문서로 BM25 인덱스를 1회 빌드해 키워드 쪽을 맡는다. 두 결과를
정규화해 가중 합산하고 상위 후보를 반환한다.
"""

from __future__ import annotations

from typing import Any

from .bm25_retriever import BM25Retriever


class EnsembleRetriever:
    """BM25와 ChromaDB 벡터 검색을 합치는 하이브리드 리트리버."""

    def __init__(self, collection: Any, alpha: float = 0.5) -> None:
        """collection: ChromaDB Collection. alpha: Vector 가중치 (0.0=BM25만, 1.0=Vector만)."""
        self.collection = collection
        self.alpha = alpha
        self._bm25: BM25Retriever | None = None

    # ── internal ────────────────────────────────────────────────
    def _get_bm25(self) -> BM25Retriever | None:
        """ChromaDB에서 전체 문서를 꺼내 BM25 인덱스를 1회 빌드해 캐시한다."""
        if self._bm25 is not None:
            return self._bm25
        data = self.collection.get()
        docs = data.get("documents") or []
        metas = data.get("metadatas") or [{} for _ in docs]
        if not docs:
            return None
        self._bm25 = BM25Retriever(documents=list(docs), metadatas=list(metas))
        return self._bm25

    @staticmethod
    def _normalize(hits: list[dict]) -> list[dict]:
        if not hits:
            return hits
        scores = [h["score"] for h in hits]
        lo, hi = min(scores), max(scores)
        rng = hi - lo
        for h in hits:
            h["normalized_score"] = (h["score"] - lo) / rng if rng > 0 else 1.0
        return hits

    def _vector_search(self, query: str, fetch: int) -> list[dict]:
        try:
            res = self.collection.query(query_texts=[query], n_results=fetch)
        except Exception:
            return []
        if not res.get("documents") or not res["documents"][0]:
            return []
        hits: list[dict] = []
        for doc, meta, dist in zip(
            res["documents"][0], res["metadatas"][0], res["distances"][0]
        ):
            hits.append({
                "content": doc,
                "metadata": meta or {},
                "score": 1.0 - float(dist),
            })
        return self._normalize(hits)

    def _bm25_search(self, query: str, fetch: int) -> list[dict]:
        bm25 = self._get_bm25()
        if bm25 is None:
            return []
        hits = bm25.search(query, top_k=fetch)
        return self._normalize(hits)

    def _merge(self, vector_hits: list[dict], bm25_hits: list[dict]) -> list[dict]:
        merged: dict[str, dict] = {}
        for r in vector_hits:
            merged[r["content"]] = {
                "content": r["content"],
                "metadata": r["metadata"],
                "vector_score": r.get("normalized_score", 0.0),
                "bm25_score": 0.0,
            }
        for r in bm25_hits:
            key = r["content"]
            if key in merged:
                merged[key]["bm25_score"] = r.get("normalized_score", 0.0)
            else:
                merged[key] = {
                    "content": r["content"],
                    "metadata": r["metadata"],
                    "vector_score": 0.0,
                    "bm25_score": r.get("normalized_score", 0.0),
                }
        combined = []
        for d in merged.values():
            d["score"] = self.alpha * d["vector_score"] + (1 - self.alpha) * d["bm25_score"]
            combined.append(d)
        combined.sort(key=lambda x: x["score"], reverse=True)
        return combined

    # ── public ──────────────────────────────────────────────────
    def search(self, query: str, k: int) -> list[dict]:
        """리랭크 여유를 위해 k의 3배까지 뽑는다."""
        fetch = max(k * 3, 6)
        vector_hits = self._vector_search(query, fetch)
        bm25_hits = self._bm25_search(query, fetch)
        return self._merge(vector_hits, bm25_hits)[:fetch]
