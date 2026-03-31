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
    parser = argparse.ArgumentParser(
        description="ex08 step2 — Cross-Encoder ReRanker 실험",
    )
    parser.add_argument(
        "--max-queries",
        type=int,
        default=None,
        help="실행할 최대 쿼리 수 (기본값: 전체)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """CLI 메인 함수."""
    parser = build_parser()
    args = parser.parse_args(argv)
    run_reranker_experiment(max_queries=args.max_queries)


if __name__ == "__main__":
    main()
