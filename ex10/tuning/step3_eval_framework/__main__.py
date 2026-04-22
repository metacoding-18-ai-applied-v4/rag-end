"""step3 — RAG 평가 프레임워크 CLI.

Usage:
    python -m tuning.step3_eval_framework --strategy D --k 3
    python -m tuning.step3_eval_framework --strategy all --k 3   # A/B/C/D 자동 비교
    python -m tuning.step3_eval_framework --step 2-1             # Precision@K, Recall@K (단일 조합)
    python -m tuning.step3_eval_framework --step 2-2             # Hallucination Rate
    python -m tuning.step3_eval_framework --step compare         # K 값별 비교
    python -m tuning.step3_eval_framework --step all             # 전체 + K 비교
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console

from ._main_utils import run_compare, run_step_2_2, run_step_2_3
from .strategies import STRATEGY_ORDER

console = Console()

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def run_step_2_1(k: int, strategy_name: str) -> dict | None:
    """Step 2-1: Precision@K, Recall@K 평가 (단일 조합)."""
    from .display import show_question_details
    from .evaluator import run_evaluation

    console.print(f"[bold]Step 2-1: Precision@K & Recall@K (strategy={strategy_name})[/bold]")

    result = run_evaluation(k=k, strategy_name=strategy_name)
    if "error" in result:
        console.print(f"[red]{result['error']}[/red]")
        return None

    summary = result["summary"]
    console.print(f"  조합: {result['strategy_label']} — {result['strategy_description']}")
    console.print(f"  Precision@{k}: {summary['avg_precision_at_k']:.3f}")
    console.print(f"  Recall@{k}:    {summary['avg_recall_at_k']:.3f}")
    console.print(f"  Latency:       {summary['latency_ms_per_query']:.1f} ms/질문")

    show_question_details(result, limit=5)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Step 3: RAG 평가 프레임워크")
    parser.add_argument(
        "--strategy",
        default=None,
        help="평가 조합 (A, B, C, D, all). all이면 4개 조합 자동 비교. 지정하지 않으면 --step 흐름 사용",
    )
    parser.add_argument(
        "--step",
        choices=["2-1", "2-2", "2-3", "compare", "all"],
        default=None,
        help="단일 지표 흐름 (strategy를 쓰지 않을 때)",
    )
    parser.add_argument("--k", type=int, default=3, help="검색 결과 수 K (기본: 3)")

    args = parser.parse_args()

    console.print("[bold]ex10 Step 3: RAG 평가 프레임워크[/bold]")

    # --strategy가 지정되면 조합 기반 실행
    if args.strategy:
        if args.strategy == "all":
            from .display import show_strategy_comparison, show_summary
            from .evaluator import run_all_strategies

            console.print(f"[bold]4개 조합(A/B/C/D) 비교 평가 · k={args.k}[/bold]")
            results = run_all_strategies(k=args.k)
            show_strategy_comparison(results)
            return

        if args.strategy not in STRATEGY_ORDER:
            console.print(
                f"[red]알 수 없는 strategy '{args.strategy}'. "
                f"사용 가능: {', '.join(STRATEGY_ORDER)}, all[/red]"
            )
            sys.exit(1)

        from .display import show_category_stats, show_question_details, show_summary
        from .evaluator import run_evaluation

        result = run_evaluation(k=args.k, strategy_name=args.strategy)
        if "error" in result:
            console.print(f"[red]{result['error']}[/red]")
            sys.exit(1)

        console.print(
            f"[bold]조합: {result['strategy_label']} — {result['strategy_description']}[/bold]"
        )
        show_summary(result)
        show_category_stats(result)
        show_question_details(result, limit=10)
        return

    # --strategy 없으면 기존 --step 흐름(기본 조합 D로 실행)
    step = args.step or "all"
    if step == "2-1":
        run_step_2_1(args.k, "D")
    elif step == "2-2":
        run_step_2_2(args.k)
    elif step == "2-3":
        run_step_2_3(args.k)
    elif step == "compare":
        run_compare()
    elif step == "all":
        from .display import show_category_stats, show_question_details, show_summary
        from .evaluator import run_evaluation

        result = run_evaluation(k=args.k, strategy_name="D")
        if "error" in result:
            console.print(f"[red]{result['error']}[/red]")
            sys.exit(1)

        show_summary(result)
        show_category_stats(result)
        show_question_details(result, limit=10)


if __name__ == "__main__":
    main()
