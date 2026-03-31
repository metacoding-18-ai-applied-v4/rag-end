"""step2 Rich 출력 -- 테이블 표시 유틸리티."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

console = Console()


def show_abbreviation_results(results: list[dict]) -> None:
    """약어/동의어 확장 결과를 출력합니다."""
    console.print(f"\n[bold yellow]실험 2-1. 약어/동의어 확장[/bold yellow]")
    console.print("  [dim]원리: 사전 기반 매핑으로 약어와 동의어를 정규 표현으로 치환[/dim]\n")

    table = Table(title="약어/동의어 확장 결과")
    table.add_column("원본 쿼리", style="yellow", max_width=30)
    table.add_column("확장된 쿼리", style="green", max_width=40)
    table.add_column("적용 규칙", style="cyan", max_width=40)

    for r in results:
        applied_str = "\n".join(r["applied"]) if r["applied"] else "(변경 없음)"
        table.add_row(r["original"], r["expanded"], applied_str)

    console.print(table)


def show_hyde_results(result: dict) -> None:
    """HyDE vs 직접 검색 비교 결과를 출력합니다."""
    console.print(f"\n[bold yellow]실험 2-2. HyDE (Hypothetical Document Embeddings)[/bold yellow]")
    console.print("  [dim]원리: 가상 답변 문서 생성 -> 그 문서와 유사한 실제 문서 검색[/dim]")
    console.print(f"  [bold]쿼리:[/bold] {result['query']}")
    console.print(f"  [dim]가상 문서: {result['hypothetical_doc'][:80]}...[/dim]\n")

    # 직접 검색 테이블
    direct_table = Table(title="직접 검색 결과")
    direct_table.add_column("순위", justify="center", width=4)
    direct_table.add_column("내용", style="white", max_width=50)
    direct_table.add_column("출처", style="cyan")
    direct_table.add_column("유사도", style="magenta", justify="right")

    for i, r in enumerate(result["direct_results"], 1):
        direct_table.add_row(
            str(i),
            r["content"][:60] + ("..." if len(r["content"]) > 60 else ""),
            r["source"],
            f"{r['score']:.4f}",
        )
    console.print(direct_table)

    # HyDE 검색 테이블
    hyde_table = Table(title="HyDE 검색 결과")
    hyde_table.add_column("순위", justify="center", width=4)
    hyde_table.add_column("내용", style="white", max_width=50)
    hyde_table.add_column("출처", style="cyan")
    hyde_table.add_column("유사도", style="magenta", justify="right")

    for i, r in enumerate(result["hyde_results"], 1):
        hyde_table.add_row(
            str(i),
            r["content"][:60] + ("..." if len(r["content"]) > 60 else ""),
            r["source"],
            f"{r['score']:.4f}",
        )
    console.print(hyde_table)


def show_multi_query_results(
    original_query: str,
    generated_queries: list[str],
    search_results: list[dict],
) -> None:
    """Multi-Query 결과를 출력합니다."""
    console.print(f"\n[bold yellow]실험 2-3. Multi-Query[/bold yellow]")
    console.print("  [dim]원리: 1개 질문 -> N개 다양한 표현으로 검색 결과 다양화[/dim]")
    console.print(f"  [bold]원본 쿼리:[/bold] {original_query}\n")

    # 생성된 쿼리 테이블
    q_table = Table(title="생성된 쿼리")
    q_table.add_column("번호", justify="center", width=4)
    q_table.add_column("쿼리", style="white")
    q_table.add_column("유형", style="cyan")

    for i, q in enumerate(generated_queries, 1):
        label = "원본" if i == 1 else f"변형 {i - 1}"
        q_table.add_row(str(i), q, label)
    console.print(q_table)

    # 병합 검색 결과 테이블
    r_table = Table(title="Multi-Query 병합 검색 결과")
    r_table.add_column("순위", justify="center", width=4)
    r_table.add_column("내용", style="white", max_width=50)
    r_table.add_column("출처", style="cyan")
    r_table.add_column("최고 유사도", style="magenta", justify="right")

    for i, r in enumerate(search_results, 1):
        r_table.add_row(
            str(i),
            r["content"][:60] + ("..." if len(r["content"]) > 60 else ""),
            r.get("source", ""),
            f"{r['score']:.4f}",
        )
    console.print(r_table)


def show_summary() -> None:
    """Query Rewrite 기법 비교 요약 테이블을 출력합니다."""
    table = Table(title="Query Rewrite 기법 비교")
    table.add_column("기법", style="cyan")
    table.add_column("핵심 원리", style="white")
    table.add_column("적용 상황", style="yellow")
    table.add_column("LLM 필요", style="magenta")

    table.add_row(
        "약어/동의어 확장", "사전 기반 매핑",
        "전문 용어/약어 많은 도메인", "불필요",
    )
    table.add_row(
        "HyDE", "가상 문서 임베딩",
        "답변이 구체적인 사실 문서 검색", "필요 (fallback 가능)",
    )
    table.add_row(
        "Multi-Query", "다각도 질문 변환",
        "포괄적 정보 수집 필요", "필요 (fallback 가능)",
    )

    console.print(table)
