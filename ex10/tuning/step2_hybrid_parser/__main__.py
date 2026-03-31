"""step2 — 하이브리드 파싱 CLI.

Usage:
    python -m tuning.step2_hybrid_parser --step 2-1          # OCR→Vision 하이브리드
    python -m tuning.step2_hybrid_parser --step 2-2          # 텍스트레이어→Vision
    python -m tuning.step2_hybrid_parser --step all          # 둘 다 + 비교
    python -m tuning.step2_hybrid_parser --step all --pdf ./data/docs/test.pdf --threshold 80
"""

import argparse
import sys
import time
from pathlib import Path

import fitz  # PyMuPDF
from rich.console import Console

console = Console()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


def _find_pdf(pdf_path: str | None) -> Path | None:
    """테스트용 PDF를 찾는다."""
    if pdf_path:
        p = Path(pdf_path)
        if p.exists():
            return p
        console.print(f"[red]PDF 파일을 찾을 수 없습니다: {pdf_path}[/red]")
        return None

    docs_dir = DATA_DIR / "docs"
    if docs_dir.exists():
        pdfs = list(docs_dir.rglob("*.pdf"))
        if pdfs:
            return pdfs[0]

    pdfs = list(DATA_DIR.glob("*.pdf"))
    if pdfs:
        return pdfs[0]

    console.print("[yellow]PDF 파일이 없습니다. --pdf 옵션으로 지정하세요.[/yellow]")
    return None


def run_step_2_1(pdf_path: Path, threshold: int) -> list[dict]:
    """Step 2-1: OCR → Vision LLM 하이브리드 파싱."""
    from .display import show_page_result, show_summary
    from .hybrid_parser import process_image_hybrid

    console.print("[bold]Step 2-1: 하이브리드 파싱 (OCR → Vision)[/bold]")
    console.print(f"  대상: {pdf_path.name}  |  임계값: {threshold}자")

    doc = fitz.open(str(pdf_path))
    results = []

    start = time.time()
    for page_num in range(len(doc)):
        page = doc[page_num]
        result = process_image_hybrid(page, threshold=threshold)
        results.append(result)
        show_page_result(result, page_num + 1)

    elapsed = time.time() - start
    doc.close()

    console.print(f"\n  총 소요 시간: {elapsed:.2f}초")
    show_summary(results, pdf_path.name, "하이브리드(OCR→Vision)")
    return results


def run_step_2_2(pdf_path: Path) -> list[dict]:
    """Step 2-2: 텍스트 레이어 → Vision LLM 파싱."""
    from .display import show_page_result, show_summary
    from .hybrid_parser import process_image_textlayer

    console.print("[bold]Step 2-2: 텍스트 레이어 → Vision 파싱[/bold]")
    console.print(f"  대상: {pdf_path.name}")

    doc = fitz.open(str(pdf_path))
    results = []

    start = time.time()
    for page_num in range(len(doc)):
        page = doc[page_num]
        result = process_image_textlayer(page)
        results.append(result)
        show_page_result(result, page_num + 1)

    elapsed = time.time() - start
    doc.close()

    console.print(f"\n  총 소요 시간: {elapsed:.2f}초")
    show_summary(results, pdf_path.name, "텍스트레이어→Vision")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Step 2: 하이브리드 파싱 전략")
    parser.add_argument(
        "--step",
        choices=["2-1", "2-2", "all"],
        default="all",
        help="실행할 스텝 (2-1: OCR→Vision, 2-2: TextLayer→Vision, all: 둘 다)",
    )
    parser.add_argument("--pdf", type=str, default=None, help="테스트 PDF 경로")
    parser.add_argument("--threshold", type=int, default=50, help="OCR 텍스트 임계값 (기본: 50)")

    args = parser.parse_args()

    pdf_path = _find_pdf(args.pdf)
    if not pdf_path:
        sys.exit(1)

    console.print("[bold]ex10 Step 2: 하이브리드 파싱 전략[/bold]")

    if args.step in ("2-1", "all"):
        run_step_2_1(pdf_path, args.threshold)

    if args.step in ("2-2", "all"):
        run_step_2_2(pdf_path)



if __name__ == "__main__":
    main()
