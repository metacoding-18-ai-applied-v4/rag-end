"""step3 — RAG 평가 프레임워크 CLI.

Usage:
    python -m tuning.step3_eval_framework --step 2-1          # Precision@K, Recall@K
    python -m tuning.step3_eval_framework --step 2-2          # Hallucination Rate
    python -m tuning.step3_eval_framework --step 2-3          # MRR
    python -m tuning.step3_eval_framework --step compare      # K 값별 비교
    python -m tuning.step3_eval_framework --step all          # 전체 평가
    python -m tuning.step3_eval_framework --step all --k 5
"""

import argparse
import sys
from pathlib import Path

from rich.console import Console

from ._main_utils import run_compare, run_step_2_2, run_step_2_3

console = Console()

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def run_step_2_1(k: int) -> dict | None:
    """Step 2-1: Precision@K, Recall@K 평가."""
    from .display import show_question_details, show_summary
    from .evaluator import run_evaluation

    console.print("[bold]Step 2-1: Precision@K & Recall@K[/bold]")

    result = run_evaluation(k=k)
    if "error" in result:
        console.print(f"[red]{result['error']}[/red]")
        return None

    summary = result["summary"]
    console.print(f"  Precision@{k}: {summary['avg_precision_at_k']:.3f}")
    console.print(f"  Recall@{k}:    {summary['avg_recall_at_k']:.3f}")

    show_question_details(result, limit=5)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Step 3: RAG 평가 프레임워크")
    parser.add_argument(
        "--step",
        choices=["2-1", "2-2", "2-3", "compare", "all"],
        default="all",
        help="실행할 스텝",
    )
    parser.add_argument("--k", type=int, default=3, help="검색 결과 수 K (기본: 3)")

    args = parser.parse_args()

    console.print("[bold]ex10 Step 3: RAG 평가 프레임워크[/bold]")

    if args.step == "2-1":
        run_step_2_1(args.k)
    elif args.step == "2-2":
        run_step_2_2(args.k)
    elif args.step == "2-3":
        run_step_2_3(args.k)
    elif args.step == "compare":
        run_compare()
    elif args.step == "all":
        from .display import show_category_stats, show_question_details, show_summary
        from .evaluator import run_evaluation

        result = run_evaluation(k=args.k)
        if "error" in result:
            console.print(f"[red]{result['error']}[/red]")
            sys.exit(1)

        show_summary(result)
        show_category_stats(result)
        show_question_details(result, limit=10)

        console.print()
        run_compare()



if __name__ == "__main__":
    main()
