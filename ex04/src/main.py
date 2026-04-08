"""
ex04 VectorDB 구축 파이프라인 메인 오케스트레이터.

Step 1 (Python 파싱) → Step 2 (청킹 + 임베딩 + ChromaDB 저장) → Step 3 (CLI 검증)
세 단계를 순서대로 또는 선택적으로 실행합니다.

실행 예시:
    # 전체 파이프라인 실행
    python src/main.py

    # Step 1만 실행 (Python 파싱 테스트)
    python src/main.py --step 1

    # 문서 디렉토리 변경
    python src/main.py --docs-dir ./custom_docs
"""

import sys
import time
from pathlib import Path

# src/ 디렉토리를 파이썬 경로에 추가 (모듈 임포트 지원)
sys.path.insert(0, str(Path(__file__).parent))

from _pipeline_utils import save_results_as_markdown, parse_arguments, _rel_path
from chunker import chunk_all_documents, DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP
from extractor import extract_all_from_directory
from store import (
    DEFAULT_CHROMA_DIR,
    DEFAULT_COLLECTION_NAME,
    DEFAULT_EMBEDDING_MODEL,
    store_chunks_to_chroma,
)

# 기본 경로 설정
BASE_DIR = Path(__file__).parent.parent
DEFAULT_DOCS_DIR = str(BASE_DIR / "data" / "docs")
DEFAULT_MARKDOWN_DIR = str(BASE_DIR / "data" / "markdown")




def step1_python_parsing(docs_dir: str) -> list[dict]:
    """Step 1: Python 라이브러리로 문서 텍스트를 추출합니다.

    pypdf, python-docx, openpyxl을 사용하여 docs_dir 내의 모든
    PDF, DOCX, XLSX 파일에서 텍스트를 추출합니다.

    Python 파싱의 한계:
    - 이미지 기반 PDF: 텍스트를 거의 추출하지 못합니다.
    - 복잡한 다단 레이아웃: 텍스트 순서가 뒤섞일 수 있습니다.
    - 표 안의 이미지: 추출 불가합니다.
    이미지형 PDF의 텍스트 손실 문제는 OCR이나 Vision LLM을 활용하면 개선할 수 있습니다.

    Args:
        docs_dir: 문서 파일이 저장된 디렉토리 경로

    Returns:
        문서 추출 결과 딕셔너리 리스트
    """
    print("\n" + "=" * 60)
    print("  📝 Step 1: Python 파싱 — 형식별 텍스트 추출")
    print("=" * 60)
    print(f"  📁 문서 디렉토리: {_rel_path(docs_dir)}\n")

    # TODO: extract_all_from_directory()로 문서 추출 → 결과 출력 → 마크다운 저장
    start_time = time.time()
    results = extract_all_from_directory(docs_dir)
    elapsed = time.time() - start_time

    print(f"\n  ✅ Step 1 완료: {len(results)}개 문서 추출 ({elapsed:.1f}초)")

    # 마크다운 파일 저장
    print("\n  [마크다운 변환]")
    save_results_as_markdown(results)
    print(f"    📁 저장 위치: data/markdown/")

    return results


def step2_embed_and_store(
    python_results: list[dict],
    chroma_dir: str,
    collection_name: str,
    embedding_model_name: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> dict:
    """Step 2: 추출 결과를 청킹 후 임베딩하여 ChromaDB에 저장합니다.

    Step 1(Python 파싱) 결과를 청킹하고 ko-sroberta-multitask 임베딩
    모델로 벡터를 생성하여 ChromaDB에 영속 저장합니다.

    Args:
        python_results: Step 1 추출 결과 리스트
        chroma_dir: ChromaDB 저장 디렉토리 경로
        collection_name: ChromaDB 컬렉션명
        embedding_model_name: 임베딩 모델 HuggingFace ID
        chunk_size: 텍스트 청크 최대 문자 수
        overlap: 청크 간 오버랩 문자 수

    Returns:
        store_chunks_to_chroma() 반환값 딕셔너리
    """
    print("\n" + "=" * 60)
    print("  ✂️  Step 2: 청킹 + 임베딩 + ChromaDB 저장")
    print("=" * 60)
    print(f"  📐 청크 크기: {chunk_size}자, 오버랩: {overlap}자")
    print(f"  🧮 임베딩 모델: {embedding_model_name}")
    print(f"  💾 ChromaDB: {_rel_path(chroma_dir)}\n")

    # TODO: chunk_all_documents()로 청킹 → store_chunks_to_chroma()로 ChromaDB 저장
    print("  ✂️  청킹 중...")
    all_chunks = chunk_all_documents(python_results, chunk_size, overlap)

    if not all_chunks:
        print("  ❌ 생성된 청크가 없습니다. 문서가 비어 있는지 확인하십시오.")
        sys.exit(1)

    start_time = time.time()
    store_result = store_chunks_to_chroma(
        chunks=all_chunks,
        chroma_dir=chroma_dir,
        collection_name=collection_name,
        embedding_model_name=embedding_model_name,
    )
    elapsed = time.time() - start_time

    print(f"\n  ✅ Step 2 완료 ({elapsed:.1f}초)")
    print(f"    📊 청크 수: {store_result['total_chunks']}개")
    print(f"    📦 컬렉션 문서 수: {store_result['collection_count']}개")
    print(f"    💾 ChromaDB: {_rel_path(store_result['chroma_dir'])}")

    return store_result


def main() -> None:
    """ex04 VectorDB 구축 파이프라인 메인 진입점.

    1. argparse로 실행 옵션 파싱
    2. 선택된 Step 순서대로 실행
    3. 최종 결과 요약 출력
    """
    args = parse_arguments()

    steps_to_run = sorted(set(args.step))

    print("\n" + "=" * 60)
    print("  🚀 사내 AI 비서 VectorDB 구축 파이프라인")
    print("=" * 60)
    print(f"  📁 문서: {_rel_path(args.docs_dir)}")

    pipeline_start = time.time()

    python_results: list[dict] = []

    # TODO: 1 in steps_to_run이면 step1_python_parsing 실행
    if 1 in steps_to_run:
        python_results = step1_python_parsing(docs_dir=args.docs_dir)

    # TODO: 2 in steps_to_run이면 step2_embed_and_store 실행
    if 2 in steps_to_run:
        # Step 1 결과 없이 Step 2만 실행하려면 파싱 먼저 수행
        if not python_results:
            print("\nStep 2 실행 전 문서 파싱이 필요합니다. Step 1을 자동으로 실행합니다.")
            python_results = step1_python_parsing(docs_dir=args.docs_dir)

        step2_embed_and_store(
            python_results=python_results,
            chroma_dir=args.chroma_dir,
            collection_name=args.collection,
            embedding_model_name=args.embedding_model,
            chunk_size=args.chunk_size,
            overlap=args.overlap,
        )

    # TODO: 총 소요 시간 출력 + 다음 단계(cli_search.py) 안내
    total_elapsed = time.time() - pipeline_start
    print("\n" + "=" * 60)
    print(f"  ✅ 파이프라인 완료! ({total_elapsed:.1f}초)")
    print("=" * 60)

    if 2 in steps_to_run:
        print("\n  💡 다음 단계: CLI 검색으로 품질을 검증하십시오.")
        print("     python src/cli_search.py --query '연차 사용 규정'")


if __name__ == "__main__":
    main()
