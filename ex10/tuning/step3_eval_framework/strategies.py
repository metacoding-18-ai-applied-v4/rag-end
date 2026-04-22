"""step3 — 평가용 튜닝 조합 정의 (완성 코드).

A/B/C/D 네 가지 조합을 `pipelines.py` 부품으로 조립한다.
evaluator.py가 strategy_name을 받아 여기서 조합을 꺼내 실행한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from . import pipelines as P


@dataclass(frozen=True)
class Strategy:
    """한 조합의 파이프라인 구성."""

    name: str
    description: str
    parse_fn: Callable
    chunk_fn: Callable
    query_transform_fn: Callable
    retrieve_fn: Callable
    rerank_fn: Callable

    @property
    def uses_rerank(self) -> bool:
        return self.rerank_fn is not P.rerank_noop


# ---------------------------------------------------------------------------
# 4가지 조합 — 그림 10-9 비교표와 1:1 대응
# ---------------------------------------------------------------------------

STRATEGIES: dict[str, Strategy] = {
    "A": Strategy(
        name="A (baseline)",
        description="페이지 청킹 + 벡터 검색",
        parse_fn=P.parse_pypdf,
        chunk_fn=P.chunk_page,
        query_transform_fn=P.query_noop,
        retrieve_fn=P.retrieve_cosine,
        rerank_fn=P.rerank_noop,
    ),
    "B": Strategy(
        name="B",
        description="단락 청킹 + 키워드 리랭킹",
        parse_fn=P.parse_pypdf,
        chunk_fn=P.chunk_semantic,
        query_transform_fn=P.query_noop,
        retrieve_fn=P.retrieve_cosine,
        rerank_fn=P.rerank_keyword,
    ),
    "C": Strategy(
        name="C",
        description="B + 약어 확장 + Parent Doc",
        parse_fn=P.parse_pypdf,
        chunk_fn=P.chunk_semantic,
        query_transform_fn=P.query_expand_abbreviations,
        retrieve_fn=P.retrieve_parent_doc,
        rerank_fn=P.rerank_keyword,
    ),
    "D": Strategy(
        name="D",
        description="C + 하이브리드 파서",
        parse_fn=P.parse_hybrid,
        chunk_fn=P.chunk_semantic,
        query_transform_fn=P.query_expand_abbreviations,
        retrieve_fn=P.retrieve_parent_doc,
        rerank_fn=P.rerank_keyword,
    ),
}


STRATEGY_ORDER = ["A", "B", "C", "D"]


def get_strategy(name: str) -> Strategy:
    """이름으로 조합을 꺼낸다. 없으면 ValueError."""
    if name not in STRATEGIES:
        valid = ", ".join(STRATEGY_ORDER)
        raise ValueError(f"Unknown strategy '{name}'. Use one of: {valid}")
    return STRATEGIES[name]
