"""step3 — Rich 기반 평가 결과 출력."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def show_summary(eval_result: dict) -> None:
    """전체 평가 요약을 출력한다."""
    # TODO: eval_result["summary"]에서 지표 추출
    # TODO: Rich Table 생성 (지표/값 2컬럼)
    # TODO: 질문 수, K 값, 문서 수, Precision@K, Recall@K, MRR, Hallucination Rate 행 추가
    summary = eval_result.get("summary", {})

    table = Table(title="RAG 평가 요약", show_lines=True)
    table.add_column("지표", style="cyan", justify="left", width=22)
    table.add_column("값", style="green", justify="right", width=12)

    table.add_row("질문 수", str(summary.get("total_questions", 0)))
    table.add_row("K 값", str(summary.get("k", 0)))
    table.add_row("문서 수 (벡터DB)", str(summary.get("document_count", 0)))
    table.add_row("Avg Precision@K", f"{summary.get('avg_precision_at_k', 0):.3f}")
    table.add_row("Avg Recall@K", f"{summary.get('avg_recall_at_k', 0):.3f}")
    table.add_row("MRR", f"{summary.get('mrr', 0):.3f}")
    table.add_row("Hallucination Rate", f"{summary.get('hallucination_rate', 0):.3f}")

    console.print(table)


def show_category_stats(eval_result: dict) -> None:
    """카테고리별 평가 결과를 출력한다."""
    # TODO: eval_result["category_stats"]에서 카테고리별 통계 추출
    # TODO: Rich Table 생성 (카테고리/질문 수/Avg Precision/Avg Recall 4컬럼)
    # TODO: 카테고리 정렬 후 행 추가
    category_stats = eval_result.get("category_stats", {})
    if not category_stats:
        return

    table = Table(title="카테고리별 평가", show_lines=True)
    table.add_column("카테고리", style="cyan", justify="center", width=12)
    table.add_column("질문 수", style="yellow", justify="right", width=8)
    table.add_column("Avg Precision", style="green", justify="right", width=14)
    table.add_column("Avg Recall", style="green", justify="right", width=14)

    for cat, stats in sorted(category_stats.items()):
        table.add_row(
            cat,
            str(stats.get("count", 0)),
            f"{stats.get('avg_precision', 0):.3f}",
            f"{stats.get('avg_recall', 0):.3f}",
        )

    console.print(table)


def show_question_details(eval_result: dict, limit: int = 10) -> None:
    """개별 질문 평가 결과를 출력한다."""
    # TODO: eval_result["question_results"]에서 질문별 결과 추출
    # TODO: Rich Table 생성 (ID/카테고리/질문/P@K/R@K/검색소스 6컬럼)
    # TODO: limit 개수만큼 행 추가
    question_results = eval_result.get("question_results", [])
    if not question_results:
        return

    table = Table(title=f"질문별 상세 결과 (상위 {limit}개)", show_lines=True)
    table.add_column("ID", style="cyan", justify="center", width=4)
    table.add_column("카테고리", style="yellow", justify="center", width=8)
    table.add_column("질문", style="white", width=30)
    table.add_column("P@K", style="green", justify="right", width=6)
    table.add_column("R@K", style="green", justify="right", width=6)
    table.add_column("검색 소스", style="dim", width=24)

    for r in question_results[:limit]:
        sources = ", ".join(r.get("retrieved_sources", [])[:2])
        if len(r.get("retrieved_sources", [])) > 2:
            sources += "..."

        table.add_row(
            str(r.get("id", "")),
            r.get("category", ""),
            r.get("query", "")[:28] + "...",
            f"{r.get('precision_at_k', 0):.2f}",
            f"{r.get('recall_at_k', 0):.2f}",
            sources,
        )

    console.print(table)


def show_comparison(results: list[dict]) -> None:
    """K 값에 따른 비교 결과를 출력한다."""
    # TODO: Rich Table 생성 (K/Precision@K/Recall@K/MRR/Hallucination 5컬럼)
    # TODO: 각 K 값별 결과를 행으로 추가
    if not results:
        return

    table = Table(title="K 값별 성능 비교", show_lines=True)
    table.add_column("K", style="cyan", justify="center", width=6)
    table.add_column("Precision@K", style="green", justify="right", width=14)
    table.add_column("Recall@K", style="green", justify="right", width=14)
    table.add_column("MRR", style="yellow", justify="right", width=10)
    table.add_column("Hallucination", style="red", justify="right", width=14)

    for r in results:
        s = r.get("summary", {})
        table.add_row(
            str(s.get("k", "")),
            f"{s.get('avg_precision_at_k', 0):.3f}",
            f"{s.get('avg_recall_at_k', 0):.3f}",
            f"{s.get('mrr', 0):.3f}",
            f"{s.get('hallucination_rate', 0):.3f}",
        )

    console.print(table)


def show_strategy_comparison(results: dict) -> None:
    """A/B/C/D 조합별 비교 결과를 한 표로 출력한다.

    results: {"A": {...}, "B": {...}, ...}  (run_all_strategies 반환값)
    """
    if not results:
        return

    table = Table(title="튜닝 조합별 평가 비교", show_lines=True)
    table.add_column("조합", style="cyan", justify="center", width=14)
    table.add_column("구성", style="white", width=36)
    table.add_column("Precision@K", style="green", justify="right", width=12)
    table.add_column("Recall@K", style="green", justify="right", width=10)
    table.add_column("환각률", style="red", justify="right", width=8)
    table.add_column("Latency(ms)", style="yellow", justify="right", width=12)

    for name, r in results.items():
        if "error" in r:
            table.add_row(
                r.get("strategy_label", name),
                "(에러)",
                "-",
                "-",
                "-",
                "-",
            )
            continue
        s = r.get("summary", {})
        table.add_row(
            r.get("strategy_label", name),
            r.get("strategy_description", ""),
            f"{s.get('avg_precision_at_k', 0):.3f}",
            f"{s.get('avg_recall_at_k', 0):.3f}",
            f"{s.get('hallucination_rate', 0):.3f}",
            f"{s.get('latency_ms_per_query', 0):.1f}",
        )

    console.print(table)
