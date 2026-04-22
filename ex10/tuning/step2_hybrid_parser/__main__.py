"""step2 — 하이브리드 파싱 CLI.

Usage:
    python -m tuning.step2_hybrid_parser
    python -m tuning.step2_hybrid_parser --pdf ./data/docs/test.pdf --threshold 80
"""

import argparse
import sys
import time
from pathlib import Path

import fitz  # PyMuPDF
from rich.console import Console

from ._main_utils import find_pdf

console = Console()


def run_step_2(pdf_path: Path, dpi: int = 150) -> list[dict]:
    """Step 2: 하이브리드 파싱 (pypdf 텍스트 있으면 그대로, 없으면 Vision)."""
    from .display import show_page_result, show_summary
    from .hybrid_parser import process_page_hybrid

    console.print("[bold]Step 2: 하이브리드 파싱 (pypdf → Vision)[/bold]")
    console.print(f"  대상: {pdf_path.name}  |  DPI: {dpi}")

    doc = fitz.open(str(pdf_path))
    results = []

    start = time.time()
    for page_num in range(len(doc)):
        page = doc[page_num]
        result = process_page_hybrid(page, dpi=dpi)
        results.append(result)
        show_page_result(result, page_num + 1)

    elapsed = time.time() - start
    doc.close()

    console.print(f"\n  총 소요 시간: {elapsed:.2f}초")
    show_summary(results, pdf_path.name, "하이브리드(pypdf→Vision)")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Step 2: 하이브리드 파싱 전략")
    parser.add_argument("--pdf", type=str, default=None, help="테스트 PDF 경로")
    parser.add_argument("--dpi", type=int, default=150, help="렌더링 DPI (기본: 150)")

    args = parser.parse_args()

    pdf_path = find_pdf(args.pdf)
    if not pdf_path:
        sys.exit(1)

    console.print("[bold]ex10 Step 2: 하이브리드 파싱 전략[/bold]")
    run_step_2(pdf_path, dpi=args.dpi)


if __name__ == "__main__":
    main()
