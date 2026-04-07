"""
검색 CLI 유틸리티 — 유사도 변환, 결과 출력, CLI 인수 파싱
cli_search.py에서 import하여 사용합니다.
"""

import argparse
import os
import re
import sys
from pathlib import Path

from store import (
    DEFAULT_CHROMA_DIR,
    DEFAULT_COLLECTION_NAME,
    DEFAULT_EMBEDDING_MODEL,
)

SEPARATOR = "=" * 60


def format_distance_as_similarity(distance: float) -> float:
    """코사인 거리를 백분율 유사도로 변환합니다.

    ChromaDB cosine 공간에서 distance 범위는 0(완전 일치)~2(완전 반대)입니다.
    직관적인 유사도 표현을 위해 (1 - distance/2) * 100 으로 변환합니다.

    Args:
        distance: ChromaDB 반환 코사인 거리 (0.0 ~ 2.0)

    Returns:
        유사도 백분율 (float, 0.0 ~ 100.0)
    """
    return max(0.0, (1.0 - distance / 2.0)) * 100


def _similarity_bar(pct: float, width: int = 20) -> str:
    """유사도 백분율을 시각적 프로그레스 바로 변환합니다."""
    filled = int(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


def _clean_text(text: str, max_len: int = 200) -> str:
    """청크 텍스트를 읽기 쉽게 정리합니다.

    연속 공백과 불필요한 줄바꿈을 제거하고 최대 길이를 제한합니다.
    """
    # 연속 공백 → 단일 공백 (PDF 다단 편집 공백 문제 해결)
    cleaned = re.sub(r"[ \t]{2,}", " ", text.strip())
    # 연속 줄바꿈 → 단일 줄바꿈
    cleaned = re.sub(r"\n{2,}", "\n", cleaned)
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len] + "..."
    return cleaned


def print_search_result(result: dict) -> None:
    """단일 검색 결과를 터미널에 이모지와 함께 출력합니다.

    Args:
        result: store.search_chroma() 반환 리스트의 개별 원소 딕셔너리
    """
    rank = result["rank"]
    text = result["text"]
    distance = result["distance"]
    meta = result["metadata"]

    pct = format_distance_as_similarity(distance)
    file_name = meta.get("file_name", "알 수 없음")
    page = meta.get("page", "-")
    chunk_type = meta.get("chunk_type", "text")
    image_path = meta.get("image_path", "")

    # 순위별 이모지
    rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")

    # 유사도별 이모지
    if pct >= 80:
        score_emoji = "🟢"
    elif pct >= 70:
        score_emoji = "🟡"
    else:
        score_emoji = "🔴"

    # 파일 유형별 이모지
    type_emoji = "🖼️" if chunk_type == "image_caption" else "📄"

    # 결과 헤더
    print(f"\n{'─' * 60}")
    print(f"  {rank_emoji}  {score_emoji} 유사도 {pct:.1f}%  {_similarity_bar(pct)}")
    print(f"  {type_emoji}  출처: {file_name}  |  페이지: {page}")
    print(f"{'─' * 60}")

    # 텍스트 근거 (정리된 버전)
    display_text = _clean_text(text)
    # 들여쓰기 적용
    for line in display_text.split("\n"):
        print(f"  {line}")

    # 이미지 캡처본 경로 표시
    if image_path:
        exists = "✅" if Path(image_path).exists() else "⚠️ 파일 없음"
        print(f"  🖼️  캡처본: {image_path} {exists}")


def parse_arguments() -> argparse.Namespace:
    """CLI 인수를 파싱합니다.

    Returns:
        파싱된 인수 네임스페이스
    """
    parser = argparse.ArgumentParser(
        description="ChromaDB 벡터 검색 CLI 도구 — 사내 문서에서 관련 근거를 검색합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python src/cli_search.py
  python src/cli_search.py --query "연차 사용 기준"
  python src/cli_search.py --query "비밀번호 정책" --top-k 3
  python src/cli_search.py --chroma-dir ./custom_db
        """,
    )

    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="검색 쿼리 (미지정 시 대화형 모드 실행)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="반환할 최대 검색 결과 수 (기본값: 5)",
    )
    parser.add_argument(
        "--chroma-dir",
        type=str,
        default=DEFAULT_CHROMA_DIR,
        help=f"ChromaDB 저장 디렉토리 경로 (기본값: {DEFAULT_CHROMA_DIR})",
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

    return parser.parse_args()
