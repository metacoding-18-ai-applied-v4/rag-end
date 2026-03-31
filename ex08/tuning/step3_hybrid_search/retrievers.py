"""BM25Retriever / VectorRetriever / EnsembleRetriever 클래스."""

from __future__ import annotations

import sys

from .data import EMBEDDING_MODEL
from .display import console


# ── BM25Retriever ────────────────────────────────────────────────
class BM25Retriever:
    """BM25 키워드 기반 검색기."""

    def __init__(self, documents: list[str], metadatas: list[dict] | None = None):
        self.documents = documents
        self.metadatas = metadatas or [{} for _ in documents]
        self.bm25 = self._build_index(documents)

    def _build_index(self, documents: list[str]):
        """BM25 인덱스를 빌드합니다."""
        try:
            from rank_bm25 import BM25Okapi

            tokenized_docs = [doc.lower().split() for doc in documents]
            return BM25Okapi(tokenized_docs)

        except ImportError:
            console.print("[red]rank-bm25 패키지가 설치되지 않았습니다.[/red]")
            console.print("pip install rank-bm25 를 실행하십시오.")
            sys.exit(1)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """BM25 로 문서를 검색합니다."""
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)

        scored_indices = sorted(
            enumerate(scores), key=lambda x: x[1], reverse=True
        )[:top_k]

        results = []
        for idx, score in scored_indices:
            results.append(
                {
                    "content": self.documents[idx],
                    "score": float(score),
                    "metadata": self.metadatas[idx],
                    "retriever_type": "bm25",
                }
            )
        return results


# ── VectorRetriever ──────────────────────────────────────────────
class VectorRetriever:
    """벡터 기반 시맨틱 검색기."""

    def __init__(
        self,
        documents: list[str],
        metadatas: list[dict] | None = None,
        model_name: str = EMBEDDING_MODEL,
    ):
        self.documents = documents
        self.metadatas = metadatas or [{} for _ in documents]
        self.model = self._load_model(model_name)
        self.embeddings = self._embed_documents(documents)

    def _load_model(self, model_name: str):
        """임베딩 모델을 로드합니다."""
        try:
            from sentence_transformers import SentenceTransformer

            console.print(f"[dim]임베딩 모델 로드 중: {model_name}[/dim]")
            model = SentenceTransformer(model_name)
            console.print("[green]임베딩 모델 로드 완료[/green]")
            return model

        except ImportError:
            console.print(
                "[red]sentence-transformers 패키지가 설치되지 않았습니다.[/red]"
            )
            console.print("pip install sentence-transformers 를 실행하십시오.")
            sys.exit(1)

    def _embed_documents(self, documents: list[str]):
        """문서 임베딩을 사전 계산합니다."""
        console.print("[dim]문서 임베딩 생성 중...[/dim]")
        embeddings = self.model.encode(documents, convert_to_numpy=True)
        console.print(f"[green]임베딩 생성 완료:[/green] {len(documents)}개 문서")
        return embeddings

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """코사인 유사도 기반 검색을 수행합니다."""
        import numpy as np

        query_embedding = self.model.encode([query], convert_to_numpy=True)[0]

        norms = np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(
            query_embedding
        )
        norms = np.where(norms == 0, 1e-9, norms)
        similarities = np.dot(self.embeddings, query_embedding) / norms

        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append(
                {
                    "content": self.documents[idx],
                    "score": float(similarities[idx]),
                    "metadata": self.metadatas[idx],
                    "retriever_type": "vector",
                }
            )
        return results


# ── EnsembleRetriever ────────────────────────────────────────────
class EnsembleRetriever:
    """BM25 + Vector 검색 결합 앙상블 검색기."""

    def __init__(
        self,
        bm25_retriever: BM25Retriever,
        vector_retriever: VectorRetriever,
        alpha: float = 0.5,
    ):
        """alpha: Vector 가중치 (0.0 = BM25만, 1.0 = Vector만)."""
        self.bm25_retriever = bm25_retriever
        self.vector_retriever = vector_retriever
        self.alpha = alpha

    @staticmethod
    def _normalize_scores(results: list[dict]) -> list[dict]:
        """검색 점수를 0~1 범위로 정규화합니다."""
        if not results:
            return results

        scores = [r["score"] for r in results]
        min_score, max_score = min(scores), max(scores)
        score_range = max_score - min_score

        for r in results:
            r["normalized_score"] = (
                (r["score"] - min_score) / score_range if score_range > 0 else 1.0
            )
        return results

    def search(self, query: str, top_k: int = 5, fetch_k: int = 10) -> list[dict]:
        """하이브리드 검색을 수행합니다."""
        bm25_results = self._normalize_scores(
            self.bm25_retriever.search(query, top_k=fetch_k)
        )
        vector_results = self._normalize_scores(
            self.vector_retriever.search(query, top_k=fetch_k)
        )

        doc_scores: dict[str, dict] = {}

        for result in bm25_results:
            key = result["content"]
            doc_scores[key] = {
                "content": result["content"],
                "metadata": result["metadata"],
                "bm25_score": result["normalized_score"],
                "vector_score": 0.0,
            }

        for result in vector_results:
            key = result["content"]
            if key in doc_scores:
                doc_scores[key]["vector_score"] = result["normalized_score"]
            else:
                doc_scores[key] = {
                    "content": result["content"],
                    "metadata": result["metadata"],
                    "bm25_score": 0.0,
                    "vector_score": result["normalized_score"],
                }

        final_results = []
        for doc_data in doc_scores.values():
            hybrid_score = (
                self.alpha * doc_data["vector_score"]
                + (1 - self.alpha) * doc_data["bm25_score"]
            )
            doc_data["hybrid_score"] = hybrid_score
            doc_data["retriever_type"] = "hybrid"
            final_results.append(doc_data)

        final_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return final_results[:top_k]
