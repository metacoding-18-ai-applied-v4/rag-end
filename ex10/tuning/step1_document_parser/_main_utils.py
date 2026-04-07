"""step1 — CLI 보조 함수 (완성 코드).

PDF 탐색, argparse 등 CLI 보일러플레이트를 제공한다.
"""

from pathlib import Path

from rich.console import Console

console = Console()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


def find_pdf(pdf_path: str | None) -> Path | None:
    """테스트용 PDF를 찾는다."""
    if pdf_path:
        p = Path(pdf_path)
        if p.exists():
            return p
        console.print(f"[red]PDF 파일을 찾을 수 없습니다: {pdf_path}[/red]")
        return None

    # data/docs 에서 첫 번째 PDF
    docs_dir = DATA_DIR / "docs"
    if docs_dir.exists():
        pdfs = list(docs_dir.rglob("*.pdf"))
        if pdfs:
            return pdfs[0]

    pdfs = list(DATA_DIR.glob("*.pdf"))
    if pdfs:
        return pdfs[0]

    console.print("[yellow]PDF 파일이 없습니다. --pdf_path 옵션으로 지정하세요.[/yellow]")
    return None
