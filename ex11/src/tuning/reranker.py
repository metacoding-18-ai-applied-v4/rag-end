"""CH08 리랭커 원본. sentence-transformers의 Cross-Encoder로 쿼리·문서 쌍을 채점한다.

ex11은 이 클래스를 그대로 import해 run_pipeline의 재정렬 단계에 꽂는다.
sentence-transformers 미설치 시 토큰 오버랩 기반 폴백(`SimpleReranker`)으로 자동 전환.
"""

from __future__ import annotations

import sys

CROSS_ENCODER_MODEL = "BAAI/bge-reranker-v2-m3"


class CrossEncoderReranker:
    """Cross-Encoder 기반 리랭커 (CH08 step2_reranker 원본)."""

    def __init__(self, model_name: str = CROSS_ENCODER_MODEL) -> None:
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        try:
            from sentence_transformers import CrossEncoder

            self.model = CrossEncoder(self.model_name)
        except ImportError:
            print("[reranker] sentence-transformers 미설치 → SimpleReranker로 폴백", file=sys.stderr)
            self.model = None
        except Exception as exc:
            print(f"[reranker] 모델 로드 실패: {exc} → SimpleReranker로 폴백", file=sys.stderr)
            self.model = None

    def rerank(self, query: str, documents: list[dict], top_k: int = 5) -> list[dict]:
        if self.model is None:
            return SimpleReranker().rerank(query, documents, top_k)

        pairs = [(query, doc["content"]) for doc in documents]
        scores = self.model.predict(pairs)
        for doc, score in zip(documents, scores):
            doc["cross_encoder_score"] = float(score)

        ordered = sorted(
            documents,
            key=lambda d: d.get("cross_encoder_score", 0.0),
            reverse=True,
        )
        return ordered[:top_k]


class SimpleReranker:
    """Cross-Encoder 없이 동작하는 키워드 오버랩 폴백 (CH08 원본)."""

    def rerank(self, query: str, documents: list[dict], top_k: int = 5) -> list[dict]:
        query_words = set(query.lower().split())
        for doc in documents:
            doc_words = set(doc["content"].lower().split())
            overlap = len(query_words & doc_words) / len(query_words) if query_words else 0.0
            doc["cross_encoder_score"] = overlap
        ordered = sorted(
            documents,
            key=lambda d: d.get("cross_encoder_score", 0.0),
            reverse=True,
        )
        return ordered[:top_k]
