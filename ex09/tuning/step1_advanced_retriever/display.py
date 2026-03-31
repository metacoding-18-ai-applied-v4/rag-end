"""step1 Rich 출력 -- 테이블 표시 유틸리티."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

console = Console()


def show_parent_doc_results(results: list[dict], query: str) -> None:
    """ParentDocumentRetriever 결과를 출력합니다."""
    console.print(f"\n[bold yellow]실험 1-1. ParentDocumentRetriever[/bold yellow]")
    console.print("  [dim]원리: 작은 청크로 검색 -> 원본 전체 문서 반환 (컨텍스트 풍부)[/dim]")
    console.print(f"  [bold]쿼리:[/bold] {query}\n")

    table = Table(title="ParentDocument 검색 결과")
    table.add_column("순위", justify="center", width=4)
    table.add_column("매칭 청크", style="yellow", max_width=40)
    table.add_column("부모 문서", style="cyan", max_width=20)
    table.add_column("부모 길이", style="green", justify="right")
    table.add_column("유사도", style="magenta", justify="right")

    for i, r in enumerate(results, 1):
        table.add_row(
            str(i),
            r["child_chunk"],
            r.get("parent_title", r["metadata"].get("source", "")),
            f"{len(r['parent_content'])}자",
            f"{r['score']:.4f}",
        )

    console.print(table)


def show_self_query_results(results: list[dict], query: str) -> None:
    """SelfQueryRetriever 결과를 출력합니다."""
    console.print(f"\n[bold yellow]실험 1-2. SelfQueryRetriever[/bold yellow]")
    console.print("  [dim]원리: LLM이 질문에서 메타데이터 필터 자동 추출 -> 정확한 필터링[/dim]")
    console.print(f"  [bold]쿼리:[/bold] {query}\n")

    if results:
        applied = results[0].get("applied_filter", {})
        console.print(f"  [dim]자동 추출된 필터: {applied}[/dim]\n")

    table = Table(title="SelfQuery 검색 결과")
    table.add_column("순위", justify="center", width=4)
    table.add_column("내용", style="white", max_width=50)
    table.add_column("토픽", style="cyan")
    table.add_column("유사도", style="magenta", justify="right")

    for i, r in enumerate(results, 1):
        table.add_row(
            str(i),
            r["content"][:60] + ("..." if len(r["content"]) > 60 else ""),
            r["metadata"].get("topic", "-"),
            f"{r['score']:.4f}",
        )

    console.print(table)


def show_compression_results(results: list[dict], query: str) -> None:
    """ContextualCompressionRetriever 결과를 출력합니다."""
    console.print(f"\n[bold yellow]실험 1-3. ContextualCompressionRetriever[/bold yellow]")
    console.print("  [dim]원리: 검색된 문서에서 쿼리 관련 부분만 추출 -> LLM 토큰 절약[/dim]")
    console.print(f"  [bold]쿼리:[/bold] {query}\n")

    table = Table(title="Contextual Compression 결과")
    table.add_column("순위", justify="center", width=4)
    table.add_column("원본 길이", style="yellow", justify="right")
    table.add_column("압축 길이", style="green", justify="right")
    table.add_column("압축률", style="cyan", justify="right")
    table.add_column("압축된 내용", style="white", max_width=50)

    for i, r in enumerate(results, 1):
        table.add_row(
            str(i),
            f"{len(r['original_content'])}자",
            f"{len(r['compressed_content'])}자",
            f"{r['compression_ratio']:.0%}",
            r["compressed_content"][:60] + "...",
        )

    console.print(table)


def show_summary() -> None:
    """고급 Retriever 비교 요약 테이블을 출력합니다."""
    table = Table(title="고급 Retriever 비교 요약")
    table.add_column("Retriever", style="cyan")
    table.add_column("핵심 원리", style="white")
    table.add_column("장점", style="green")
    table.add_column("단점", style="red")
    table.add_column("추천 상황", style="yellow")

    table.add_row(
        "ParentDocument", "소->대 역매핑",
        "풍부한 컨텍스트", "토큰 소모 증가", "긴 문서, 문맥 중요",
    )
    table.add_row(
        "SelfQuery", "LLM 필터 추출",
        "자동 메타 필터링", "LLM 추가 호출", "구조화된 메타데이터",
    )
    table.add_row(
        "Compression", "관련 문장만 추출",
        "토큰 절약", "정보 손실 위험", "긴 문서, 토큰 제한",
    )

    console.print(table)
