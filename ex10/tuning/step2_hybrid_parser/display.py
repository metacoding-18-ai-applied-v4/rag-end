"""step2 — Rich 기반 하이브리드 파싱 결과 출력."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def show_page_result(result: dict, page_num: int) -> None:
    """단일 페이지 하이브리드 파싱 결과를 출력한다."""
    strategy = result.get("strategy", "unknown")
    char_count = result.get("char_count", 0)
    text = result.get("text", "")
    preview = text[:200].replace("\n", " ") + ("..." if len(text) > 200 else "")

    color = "yellow" if strategy == "ocr" else "green" if strategy == "vision" else "cyan"
    console.print(
        f"  Page {page_num}: [{color}]{strategy}[/{color}] "
        f"({char_count:,}자)"
    )
    if preview:
        console.print(f"    [dim]{preview}[/dim]")


def show_summary(results: list[dict], pdf_name: str, strategy_name: str) -> None:
    """전체 페이지 결과를 요약 테이블로 출력한다."""
    table = Table(
        title=f"{strategy_name} 결과 — {pdf_name}",
        show_lines=True,
    )
    table.add_column("페이지", style="cyan", justify="center", width=8)
    table.add_column("전략", style="yellow", justify="center", width=12)
    table.add_column("글자 수", style="green", justify="right", width=10)
    table.add_column("미리보기", style="white", width=40)

    strategy_counts = {"ocr": 0, "vision": 0, "text_layer": 0}

    for i, r in enumerate(results, 1):
        strategy = r.get("strategy", "unknown")
        char_count = r.get("char_count", 0)
        preview = r.get("text", "")[:50].replace("\n", " ") + "..."

        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        color = "yellow" if strategy == "ocr" else "green" if strategy == "vision" else "cyan"
        table.add_row(
            str(i),
            f"[{color}]{strategy}[/{color}]",
            f"{char_count:,}",
            preview,
        )

    console.print(table)

    # 전략 분포 요약
    total = len(results)
    parts = []
    for s, count in strategy_counts.items():
        if count > 0:
            parts.append(f"{s}: {count}/{total}")
    console.print(f"  전략 분포: {', '.join(parts)}")
