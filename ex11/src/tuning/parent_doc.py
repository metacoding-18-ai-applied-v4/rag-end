"""챕터 9 — ParentDocumentRetriever 원본.

자식 청크 검색 결과를 받아 `parent_id` 중복을 제거하고 부모 원문을 복원해
돌려준다. 인덱싱 시점에 자식·부모를 분리해 두었기 때문에 검색 정확도는
자식에서 얻고, 답변 맥락은 부모에서 얻는다.

이 클래스는 두 가지 방식으로 쓸 수 있다.
  1) `search(query, top_k)` — 자체로 검색부터 부모 복원까지 수행 (CH09 원본 API)
  2) `resolve(ranked_children, top_k)` — 외부(Ensemble + Reranker)에서 정렬한
     자식 결과를 받아 부모로 바꿔 돌려줌. RagPipeline이 이 경로를 쓴다.
"""

from __future__ import annotations


class ParentDocumentRetriever:
    """자식 청크 기반 검색 결과를 부모 원문으로 복원한다."""

    def __init__(self, child_collection, parent_docs: dict) -> None:
        """
        child_collection : ChromaDB Collection. 자식 청크가 `parent_id` 메타데이터와 함께 저장돼 있다.
        parent_docs      : {parent_id: {"content": 페이지 전체, "source": str, "page": int}}
        """
        self.child_collection = child_collection
        self.parent_docs = parent_docs

    # CH09 원본 API ─ 검색부터 부모 복원까지 일체
    def search(self, query: str, top_k: int = 3) -> list[dict]:
        if self.child_collection is None:
            return []
        fetch = max(top_k * 3, 6)
        res = self.child_collection.query(query_texts=[query], n_results=fetch)
        if not res.get("documents") or not res["documents"][0]:
            return []
        children = [
            {
                "content": doc,
                "metadata": meta or {},
                "score": 1.0 - float(dist),
            }
            for doc, meta, dist in zip(
                res["documents"][0], res["metadatas"][0], res["distances"][0]
            )
        ]
        return self.resolve(children, top_k)

    # RagPipeline 경로 ─ 이미 정렬된 자식 목록을 받아 부모로 변환
    def resolve(self, ranked_children: list[dict], top_k: int) -> list[dict]:
        seen: set[str] = set()
        results: list[dict] = []
        for child in ranked_children:
            meta = child.get("metadata", {})
            parent_id = meta.get("parent_id")
            if not parent_id or parent_id in seen:
                continue
            parent = self.parent_docs.get(parent_id)
            if parent is None:
                continue
            seen.add(parent_id)
            score = child.get(
                "cross_encoder_score",
                child.get("score", 0.0),
            )
            results.append({
                "content": parent["content"],
                "source": parent["source"],
                "page": parent["page"],
                "child_content": child.get("content", ""),
                "score": float(score),
            })
            if len(results) >= top_k:
                break
        return results
