"""
PDF 파일을 파싱하여 Markdown으로 변환하고 data/markdown/에 저장하는 스크립트.

실행 방법:
    python src/extract_pdf.py
    python src/extract_pdf.py --docs-dir ./data/docs
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from extractor import extract_from_pdf

# 기본 경로
BASE_DIR = Path(__file__).parent.parent
DOCS_DIR = BASE_DIR / "data" / "docs"
MARKDOWN_DIR = BASE_DIR / "data" / "markdown"


def save_as_markdown(result: dict, output_dir: Path) -> Path:
    """추출 결과를 Markdown 파일로 저장합니다.

    Args:
        result: extractor.extract_from_pdf() 반환값
        output_dir: Markdown 파일 저장 디렉토리

    Returns:
        저장된 Markdown 파일 경로
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(result["file_name"]).stem
    md_path = output_dir / f"{stem}.md"

    lines = []
    lines.append(f"# {result['file_name']}\n")
    lines.append(f"- 파일 형식: {result['file_type']}")
    lines.append(f"- 총 페이지: {len(result['pages'])}페이지")
    lines.append(f"- 추출 글자 수: {len(result['full_text'])}자")
    lines.append(f"- 원본 경로: `{result['source_path']}`\n")
    lines.append("---\n")

    for page in result["pages"]:
        text = page["text"]
        if not text:
            continue
        lines.append(text)
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def main() -> None:
    """data/docs/에서 모든 PDF를 찾아 파싱하고 Markdown으로 저장합니다."""
    print("\n" + "=" * 60)
    print("  📝 PDF 파싱 → Markdown 변환")
    print("=" * 60)

    # PDF 파일 수집
    pdf_files = sorted(DOCS_DIR.rglob("*.pdf"))
    if not pdf_files:
        print(f"  ❌ PDF 파일이 없습니다: {DOCS_DIR}")
        sys.exit(1)

    print(f"  📁 문서: data/docs/")
    print(f"  📄 PDF 파일: {len(pdf_files)}개\n")

    start_time = time.time()
    results = []

    for file_path in pdf_files:
        result = extract_from_pdf(file_path)
        md_path = save_as_markdown(result, MARKDOWN_DIR)
        text_len = len(result["full_text"])
        page_count = len(result["pages"])
        emoji = "⚠️" if text_len == 0 else "✅"
        print(f"  {emoji} {file_path.name} → {md_path.name} ({page_count}페이지, {text_len}자)")
        results.append(result)

    elapsed = time.time() - start_time
    print(f"\n  ✅ PDF 파싱 완료: {len(results)}개 ({elapsed:.1f}초)")
    print(f"  💾 저장 위치: data/markdown/")


if __name__ == "__main__":
    main()
