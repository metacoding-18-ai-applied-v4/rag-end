"""Rich Console / Table 출력 유틸리티."""

from rich.console import Console
from rich.table import Table

console = Console(force_terminal=True, width=100)


def print_comparison_tables(comparison: dict) -> None:
    """리랭킹 전후 비교 테이블을 출력합니다."""
    # TODO: comparison["query"]를 출력합니다.
    #       "리랭킹 전 (Vector Search 순위)" 테이블을 생성합니다.
    #         - 컬럼: 순위, 문서 ID, Vector 점수, 내용 미리보기
    #         - comparison["before"][:5]의 각 항목을 행으로 추가합니다.
    #       "리랭킹 후 (Cross-Encoder 순위)" 테이블을 생성합니다.
    #         - 컬럼: 순위, 문서 ID, CE 점수, 내용 미리보기
    #         - comparison["after"]의 각 항목을 행으로 추가합니다.
    #       두 테이블을 console.print()로 출력합니다.
    console.print(f"\n[bold]쿼리:[/bold] {comparison['query']}")

    # 리랭킹 전
    before_table = Table(title="리랭킹 전 (Vector Search 순위)")
    before_table.add_column("순위", style="cyan", justify="center")
    before_table.add_column("문서 ID", style="yellow")
    before_table.add_column("Vector 점수", style="green")
    before_table.add_column("내용 미리보기", style="white")

    for item in comparison["before"][:5]:
        before_table.add_row(
            str(item["rank"]),
            item["id"],
            f"{item['score']:.3f}",
            item["content_preview"],
        )

    # 리랭킹 후
    after_table = Table(title="리랭킹 후 (Cross-Encoder 순위)")
    after_table.add_column("순위", style="cyan", justify="center")
    after_table.add_column("문서 ID", style="yellow")
    after_table.add_column("CE 점수", style="green")
    after_table.add_column("내용 미리보기", style="white")

    for item in comparison["after"]:
        after_table.add_row(
            str(item["rank"]),
            item["id"],
            f"{item['score']:.3f}",
            item["content_preview"],
        )

    console.print(before_table)
    console.print(after_table)
