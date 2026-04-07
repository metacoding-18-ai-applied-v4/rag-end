"""
파이프라인 유틸리티 — 경로 변환, 마크다운 저장, CLI 인수 파싱
main.py에서 import하여 사용합니다.
"""

import argparse
from pathlib import Path

# 기본 경로 설정
BASE_DIR = Path(__file__).parent.parent
DEFAULT_DOCS_DIR = str(BASE_DIR / "data" / "docs")
DEFAULT_MARKDOWN_DIR = str(BASE_DIR / "data" / "markdown")


def _rel_path(path_str: str) -> str:
    """절대 경로를 프로젝트 기준 상대 경로로 변환합니다."""
    try:
        return str(Path(path_str).relative_to(BASE_DIR))
    except ValueError:
        return path_str


def save_results_as_markdown(
    results: list[dict], markdown_dir: str = DEFAULT_MARKDOWN_DIR
) -> None:
    """추출 결과를 마크다운 파일로 저장합니다.

    파싱된 텍스트를 data/markdown/에 .md 파일로 저장합니다.
    임베딩 품질 향상과 사람이 파싱 결과를 확인하는 용도로 사용됩니다.

    Args:
        results: extractor.extract_all_from_directory() 반환값
        markdown_dir: 마크다운 파일 저장 디렉토리
    """
    md_dir = Path(markdown_dir)
    md_dir.mkdir(parents=True, exist_ok=True)

    for result in results:
        stem = Path(result["file_name"]).stem
        md_path = md_dir / f"{stem}.md"

        lines = [f"# {result['file_name']}\n"]
        lines.append(f"- 파일 형식: {result['file_type']}")
        lines.append(f"- 추출 글자 수: {len(result['full_text'])}자\n")
        lines.append("---\n")

        for page in result["pages"]:
            text = page.get("text", "")
            if not text:
                continue
            lines.append(text)
            lines.append("")

        md_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"    💾 {result['file_name']} → {md_path.name}")


def parse_arguments() -> argparse.Namespace:
    """CLI 인수를 파싱합니다.

    Returns:
        파싱된 인수 네임스페이스
    """
    # 순환 import 방지를 위해 여기서 import
    from store import (
        DEFAULT_CHROMA_DIR,
        DEFAULT_COLLECTION_NAME,
        DEFAULT_EMBEDDING_MODEL,
    )
    from chunker import DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP

    parser = argparse.ArgumentParser(
        description="ex04 VectorDB 구축 파이프라인 — 문서를 파싱, 청킹, 임베딩하여 ChromaDB에 저장합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
실행 예시:
  python src/main.py                     # 전체 파이프라인 (Step 1+2)
  python src/main.py --step 1            # Python 파싱만 테스트
  python src/main.py --step 1 2          # 전체 실행
        """,
    )

    parser.add_argument(
        "--step",
        type=int,
        nargs="+",
        choices=[1, 2],
        default=[1, 2],
        help="실행할 Step 번호 (기본값: 1 2 — 전체 실행)",
    )
    parser.add_argument(
        "--docs-dir",
        type=str,
        default=DEFAULT_DOCS_DIR,
        help="문서 디렉토리 경로 (기본값: data/docs)",
    )
    parser.add_argument(
        "--chroma-dir",
        type=str,
        default=DEFAULT_CHROMA_DIR,
        help=f"ChromaDB 저장 경로 (기본값: {DEFAULT_CHROMA_DIR})",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=DEFAULT_COLLECTION_NAME,
        help=f"ChromaDB 컬렉션명 (기본값: {DEFAULT_COLLECTION_NAME})",
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        default=DEFAULT_EMBEDDING_MODEL,
        help=f"임베딩 모델 HuggingFace ID (기본값: {DEFAULT_EMBEDDING_MODEL})",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"텍스트 청크 최대 문자 수 (기본값: {DEFAULT_CHUNK_SIZE})",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=DEFAULT_OVERLAP,
        help=f"청크 간 오버랩 문자 수 (기본값: {DEFAULT_OVERLAP})",
    )

    return parser.parse_args()
