"""Rich Console / Table 출력 유틸리티."""

from rich.console import Console
from rich.table import Table

console = Console(force_terminal=True, width=100)


def print_experiment_table(title: str, results: list[dict]) -> None:
    """실험 결과 딕셔너리 리스트를 Rich Table 로 출력합니다.

    Args:
        title: 테이블 상단에 표시할 제목.
        results: 동일한 키 구조를 가진 딕셔너리 리스트.
    """
    # TODO: results가 비어있으면 "결과가 없습니다" 출력 후 리턴합니다.
    #       Table(title=title)을 생성하고, results[0]의 키들로 컬럼을 추가합니다.
    #       각 result 딕셔너리의 값들을 문자열로 변환하여 행을 추가합니다.
    #       console.print(table)로 출력합니다.
    if not results:
        console.print("[red]결과가 없습니다.[/red]")
        return

    table = Table(title=title)
    for col in results[0].keys():
        table.add_column(str(col), style="cyan")

    for row in results:
        table.add_row(*[str(v) for v in row.values()])

    console.print(table)
