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
        # TODO: sentence_transformers.CrossEncoder를 import하여 self.model에 할당합니다.
        #       - ImportError 시 에러 메시지 출력 후 sys.exit(1)
        #       - 기타 Exception 시 에러 메시지 출력 후 raise
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
        # TODO: self.model이 None이면 documents[:top_k]를 그대로 반환합니다.
        #       (query, doc["content"]) 쌍을 만들어 model.predict()로 점수를 계산합니다.
        #       각 문서에 "cross_encoder_score" 키를 추가하고, 점수 내림차순 정렬 후
        #       상위 top_k개를 반환합니다.
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
        # TODO: 쿼리 단어 집합과 각 문서 단어 집합의 교집합 비율을
        #       "cross_encoder_score"로 부여합니다.
        #       점수 내림차순 정렬 후 상위 top_k개를 반환합니다.
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
    # TODO: use_simple=True이면 SimpleReranker()를 반환합니다.
    #       아니면 sentence_transformers import 시도 후 CrossEncoderReranker()를 반환합니다.
    #       ImportError 시 SimpleReranker()로 폴백합니다.
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
