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


def run_step_2_2(k: int) -> dict | None:
    """Step 2-2: Hallucination Rate 평가."""
    from .display import show_summary
    from .evaluator import run_evaluation

    console.print("[bold]Step 2-2: Hallucination Rate[/bold]")

    result = run_evaluation(k=k)
    if "error" in result:
        console.print(f"[red]{result['error']}[/red]")
        return None

    rate = result["summary"]["hallucination_rate"]
    console.print(f"  Hallucination Rate: {rate:.3f} ({rate * 100:.1f}%)")

    if rate < 0.1:
        console.print("  [green]환각 비율이 낮습니다.[/green]")
    elif rate < 0.3:
        console.print("  [yellow]환각 비율이 보통입니다. 개선이 필요합니다.[/yellow]")
    else:
        console.print("  [red]환각 비율이 높습니다. 컨텍스트 품질을 점검하세요.[/red]")

    return result


def run_step_2_3(k: int) -> dict | None:
    """Step 2-3: MRR 평가."""
    from .display import show_summary
    from .evaluator import run_evaluation

    console.print("[bold]Step 2-3: Mean Reciprocal Rank (MRR)[/bold]")

    result = run_evaluation(k=k)
    if "error" in result:
        console.print(f"[red]{result['error']}[/red]")
        return None

    mrr = result["summary"]["mrr"]
    console.print(f"  MRR: {mrr:.3f}")

    if mrr > 0.8:
        console.print("  [green]관련 문서가 상위에 잘 랭킹되고 있습니다.[/green]")
    elif mrr > 0.5:
        console.print("  [yellow]랭킹 품질이 보통입니다.[/yellow]")
    else:
        console.print("  [red]관련 문서가 하위에 위치합니다. 임베딩이나 청킹을 개선하세요.[/red]")

    return result


def run_compare() -> None:
    """K 값별 성능 비교."""
    from .display import show_comparison
    from .evaluator import run_evaluation

    console.print("[bold]K 값별 성능 비교[/bold]")

    results = []
    for k_val in [1, 3, 5, 10]:
        console.print(f"  K={k_val} 평가 중...")
        result = run_evaluation(k=k_val)
        if "error" not in result:
            results.append(result)

    if results:
        show_comparison(results)
    else:
        console.print("[red]평가에 실패했습니다.[/red]")


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
        from .display import show_category_stats, show_summary
        from .evaluator import run_evaluation

        result = run_evaluation(k=args.k)
        if "error" in result:
            console.print(f"[red]{result['error']}[/red]")
            sys.exit(1)

        show_summary(result)
        show_category_stats(result)

        from .display import show_question_details
        show_question_details(result, limit=10)

        # K 값별 비교도 함께
        console.print()
        run_compare()



if __name__ == "__main__":
    main()
