"""리랭킹 실험 유틸리티 및 실행기."""

from __future__ import annotations

import copy
import time

from .data import SAMPLE_DOCUMENTS
from .display import console, print_comparison_tables
from .reranker import create_reranker


# ── 실험 유틸리티 ────────────────────────────────────────────────
def simulate_initial_retrieval(
    query: str, documents: list[dict], top_k: int = 10
) -> list[dict]:
    """초기 벡터 검색 결과를 시뮬레이션합니다."""
    docs = copy.deepcopy(documents)
    query_words = set(query.lower().split())
    for doc in docs:
        doc_words = set(doc["content"].lower().split())
        bonus = 0.05 * len(query_words & doc_words)
        doc["score"] = min(doc["score"] + bonus, 1.0)
    docs.sort(key=lambda x: x["score"], reverse=True)
    return docs[:top_k]


def compare_before_after_reranking(
    query: str, initial_results: list[dict], reranked_results: list[dict]
) -> dict:
    """리랭킹 전후 순위를 비교합니다."""
    comparison: dict = {"query": query, "before": [], "after": []}

    for rank, doc in enumerate(initial_results, 1):
        comparison["before"].append(
            {
                "rank": rank,
                "id": doc["id"],
                "score": doc.get("score", 0.0),
                "content_preview": doc["content"][:40] + "...",
            }
        )

    for rank, doc in enumerate(reranked_results, 1):
        comparison["after"].append(
            {
                "rank": rank,
                "id": doc["id"],
                "score": doc.get("cross_encoder_score", 0.0),
                "content_preview": doc["content"][:40] + "...",
            }
        )

    return comparison


def calculate_rank_change(before: list[dict], after: list[dict]) -> list[dict]:
    """리랭킹 전후 순위 변화를 계산합니다."""
    before_ranks = {item["id"]: item["rank"] for item in before}
    after_ranks = {item["id"]: item["rank"] for item in after}

    changes = []
    for doc_id, after_rank in after_ranks.items():
        before_rank = before_ranks.get(doc_id, 99)
        change = before_rank - after_rank
        changes.append(
            {
                "문서 ID": doc_id,
                "리랭킹 전 순위": before_rank if before_rank < 99 else "신규",
                "리랭킹 후 순위": after_rank,
                "순위 변화": f"+{change}" if change > 0 else str(change),
            }
        )
    return changes


# ── 메인 실험 ────────────────────────────────────────────────────
def run_reranker_experiment(max_queries: int | None = None) -> None:
    """리랭커 실험 전체를 실행합니다.

    Args:
        max_queries: 실행할 최대 쿼리 수 (None이면 전체).
    """
    console.print("[bold]ex08 step2: ReRanker 실험[/bold]")

    reranker = create_reranker(use_simple=False)

    test_queries = [
        "연차 신청 절차는 어떻게 됩니까",
        "재택근무 신청 조건",
        "출장비 정산 기한",
    ]
    if max_queries is not None:
        test_queries = test_queries[:max_queries]

    for query in test_queries:
        console.print(f"\n[bold cyan]쿼리:[/bold cyan] {query}")

        initial_results = simulate_initial_retrieval(query, SAMPLE_DOCUMENTS, top_k=10)
        console.print(f"  초기 검색 결과: {len(initial_results)}개")

        start_time = time.time()
        reranked_results = reranker.rerank(query, initial_results, top_k=5)
        elapsed = time.time() - start_time
        console.print(f"  리랭킹 완료: {len(reranked_results)}개 ({elapsed:.3f}s)")

        comparison = compare_before_after_reranking(
            query, initial_results[:5], reranked_results
        )
        print_comparison_tables(comparison)

        calculate_rank_change(comparison["before"], comparison["after"])

    console.print(
        "\n[bold]리랭킹 효과 요약:[/bold]\n"
        "  - top_k=10으로 넓게 검색 후 Cross-Encoder로 top_k=5 정제\n"
        "  - 단순 벡터 유사도보다 질문-문서 관련성 정확도 향상\n"
        "  - 처리 시간 증가 (문서당 Cross-Encoder 추론 필요)\n"
        "  - 권장: ReRanker는 top_k가 클 때 (>10) 효과가 극대화됨"
    )
