"""step3 — CLI 보조 함수 (완성 코드).

step별 실행 함수 중 보조 로직을 제공한다.
"""

from rich.console import Console

console = Console()


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
