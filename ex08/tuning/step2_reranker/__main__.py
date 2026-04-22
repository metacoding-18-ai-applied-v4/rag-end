"""step2_reranker CLI 진입점.

사용법:
    python -m tuning.step2_reranker
    python -m tuning.step2_reranker --max-queries 1
"""

from __future__ import annotations

import argparse
import sys

from .experiments import run_reranker_experiment


def build_parser() -> argparse.ArgumentParser:
    """argparse 파서를 생성합니다."""
    # TODO: ArgumentParser를 생성하고 --max-queries (int, default=None) 인자를 추가합니다.
    parser = argparse.ArgumentParser(
        description="ex08 step2 — Cross-Encoder ReRanker 실험",
    )
    parser.add_argument(
        "--max-queries",
        type=int,
        default=None,
        help="실행할 최대 쿼리 수 (기본값: 전체)",
    )
    parser.add_argument(
        "--fetch-k",
        type=int,
        default=10,
        help="초기 검색에서 가져올 문서 수 (기본값: 10)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="리랭킹 후 최종 반환 문서 수 (기본값: 5)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """CLI 메인 함수."""
    # TODO: build_parser()로 파서 생성 → args 파싱
    #       → run_reranker_experiment(max_queries, fetch_k, top_k) 호출
    parser = build_parser()
    args = parser.parse_args(argv)
    run_reranker_experiment(
        max_queries=args.max_queries,
        fetch_k=args.fetch_k,
        top_k=args.top_k,
    )


if __name__ == "__main__":
    main()
