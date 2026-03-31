"""step1 — 문서 파싱 전략 비교 CLI.

Usage:
    python -m tuning.step1_document_parser --step 1-1          # OCR 파싱만
    python -m tuning.step1_document_parser --step 1-2          # Vision LLM 파싱만
    python -m tuning.step1_document_parser --step all          # 둘 다 + 비교
    python -m tuning.step1_document_parser --step all --pdf_path ./data/docs/test.pdf
"""

import argparse
import os
import sys
import time
from pathlib import Path

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


def run_step_1_1(pdf_path: Path) -> dict | None:
    """Step 1-1: OCR 파싱."""
    from .display import show_parse_result
    from .parser import parse_pdf_ocr

    console.print("[bold]Step 1-1: OCR 파싱 (EasyOCR)[/bold]")
    console.print(f"  대상: {pdf_path.name}")

    start = time.time()
    result = parse_pdf_ocr(pdf_path)
    elapsed = time.time() - start

    console.print(f"  소요 시간: {elapsed:.2f}초")
    show_parse_result(result, "OCR (EasyOCR)", pdf_path.name)
    return result


def run_step_1_2(pdf_path: Path) -> dict | None:
    """Step 1-2: Vision LLM 파싱."""
    from .display import show_parse_result
    from .parser import parse_pdf_vllm

    console.print("[bold]Step 1-2: Vision LLM 파싱[/bold]")
    console.print(f"  대상: {pdf_path.name}")

    start = time.time()
    result = parse_pdf_vllm(pdf_path)
    elapsed = time.time() - start

    console.print(f"  소요 시간: {elapsed:.2f}초")
    show_parse_result(result, "Vision LLM", pdf_path.name)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Step 1: 문서 파싱 전략 비교")
    parser.add_argument(
        "--step",
        choices=["1-1", "1-2", "all"],
        default="all",
        help="실행할 스텝 (1-1: OCR, 1-2: Vision LLM, all: 비교)",
    )
    parser.add_argument("--pdf_path", type=str, default=None, help="테스트 PDF 경로")
    parser.add_argument("--dpi", type=int, default=150, help="렌더링 DPI (기본: 150)")
    parser.add_argument("--timeout", type=int, default=600, help="Vision LLM 타임아웃 (초, 기본: 600)")

    args = parser.parse_args()

    pdf_path = _find_pdf(args.pdf_path)
    if not pdf_path:
        sys.exit(1)

    # --timeout CLI 인자를 환경변수로 전달 (parser.py에서 참조)
    os.environ["VISION_TIMEOUT"] = str(args.timeout)

    console.print("[bold]ex10 Step 1: 문서 파싱 전략 비교[/bold]")

    ocr_result = None
    vllm_result = None

    if args.step in ("1-1", "all"):
        ocr_result = run_step_1_1(pdf_path)

    if args.step in ("1-2", "all"):
        vllm_result = run_step_1_2(pdf_path)

    if args.step == "all" and ocr_result and vllm_result:
        from .display import show_comparison
        console.print()
        show_comparison(ocr_result, vllm_result, pdf_path.name)



if __name__ == "__main__":
    main()
