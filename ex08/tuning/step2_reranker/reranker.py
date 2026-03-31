"""CrossEncoderReranker, SimpleReranker, create_reranker."""

from __future__ import annotations

import sys

from .data import CROSS_ENCODER_MODEL
from .display import console


# ── CrossEncoderReranker ─────────────────────────────────────────
class CrossEncoderReranker:
    """Cross-Encoder 기반 리랭커."""

    def __init__(self, model_name: str = CROSS_ENCODER_MODEL):
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        """Cross-Encoder 모델을 로드합니다."""
        try:
            from sentence_transformers import CrossEncoder

            console.print(f"[dim]Cross-Encoder 모델 로드 중: {self.model_name}[/dim]")
            self.model = CrossEncoder(self.model_name)
            console.print("[green]Cross-Encoder 모델 로드 완료[/green]")

        except ImportError:
            console.print(
                "[red]sentence-transformers 패키지가 설치되지 않았습니다.[/red]"
            )
            console.print("pip install sentence-transformers 를 실행하십시오.")
            sys.exit(1)

        except Exception as e:
            console.print(f"[red]모델 로드 실패: {e}[/red]")
            console.print("[yellow]오프라인 환경이거나 모델 이름을 확인하십시오.[/yellow]")
            raise

    def rerank(self, query: str, documents: list[dict], top_k: int = 5) -> list[dict]:
        """검색 결과를 Cross-Encoder 로 재정렬합니다."""
        if self.model is None:
            console.print("[red]모델이 로드되지 않았습니다.[/red]")
            return documents[:top_k]

        pairs = [(query, doc["content"]) for doc in documents]
        scores = self.model.predict(pairs)

        for doc, score in zip(documents, scores):
            doc["cross_encoder_score"] = float(score)

        reranked = sorted(
            documents,
            key=lambda x: x.get("cross_encoder_score", 0),
            reverse=True,
        )
        return reranked[:top_k]


# ── SimpleReranker (폴백) ────────────────────────────────────────
class SimpleReranker:
    """Cross-Encoder 없이 동작하는 키워드 매칭 기반 리랭커."""

    def rerank(self, query: str, documents: list[dict], top_k: int = 5) -> list[dict]:
        """키워드 일치율로 문서를 재정렬합니다."""
        query_words = set(query.lower().split())

        for doc in documents:
            doc_words = set(doc["content"].lower().split())
            intersection = query_words & doc_words
            doc["cross_encoder_score"] = (
                len(intersection) / len(query_words) if query_words else 0.0
            )

        reranked = sorted(
            documents,
            key=lambda x: x.get("cross_encoder_score", 0),
            reverse=True,
        )
        return reranked[:top_k]


def create_reranker(use_simple: bool = False):
    """환경에 따라 적절한 리랭커를 생성합니다."""
    if use_simple:
        console.print("[cyan]SimpleReranker (키워드 기반) 사용[/cyan]")
        return SimpleReranker()

    try:
        import sentence_transformers  # noqa: F401
        return CrossEncoderReranker()
    except ImportError:
        console.print(
            "[yellow]sentence-transformers 없음. SimpleReranker로 대체합니다.[/yellow]"
        )
        return SimpleReranker()
