"""step1 — Rich 기반 결과 출력."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def show_parse_result(result: dict, strategy: str, pdf_name: str) -> None:
    """파싱 결과를 Rich Panel로 출력한다."""
    text = result.get("text", "")
    char_count = len(text)
    preview = text[:300].replace("\n", " ") + ("..." if char_count > 300 else "")

    console.print(Panel(
        f"[bold]파일:[/bold] {pdf_name}\n"
        f"[bold]전략:[/bold] {strategy}\n"
        f"[bold]추출 글자 수:[/bold] {char_count:,}자\n\n"
        f"[dim]{preview}[/dim]",
        title=f"파싱 결과 — {strategy}",
        border_style="cyan",
    ))


def show_comparison(ocr_result: dict, vllm_result: dict, pdf_name: str) -> None:
    """OCR vs Vision LLM 비교 테이블을 출력한다."""
    table = Table(
        title=f"파싱 전략 비교 — {pdf_name}",
        show_lines=True,
    )
    table.add_column("항목", style="cyan", justify="center", width=14)
    table.add_column("OCR (EasyOCR)", style="yellow", width=24)
    table.add_column("Vision LLM", style="green", width=24)

    ocr_text = ocr_result.get("text", "")
    vllm_text = vllm_result.get("text", "")

    table.add_row("글자 수", f"{len(ocr_text):,}자", f"{len(vllm_text):,}자")
    table.add_row("줄 수", f"{ocr_text.count(chr(10)):,}줄", f"{vllm_text.count(chr(10)):,}줄")

    # 표 감지
    ocr_tables = ocr_text.count("|")
    vllm_tables = vllm_text.count("|")
    table.add_row(
        "표 감지",
        f"{'있음' if ocr_tables > 5 else '없음'} ({ocr_tables}개 |)",
        f"{'있음' if vllm_tables > 5 else '없음'} ({vllm_tables}개 |)",
    )

    table.add_row(
        "미리보기",
        ocr_text[:60].replace("\n", " ") + "...",
        vllm_text[:60].replace("\n", " ") + "...",
    )

    console.print(table)
