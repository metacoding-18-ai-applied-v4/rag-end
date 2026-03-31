"""step3_hybrid_search CLI 진입점.

사용법:
    python -m tuning.step3_hybrid_search
    python -m tuning.step3_hybrid_search --max-queries 1
"""

from __future__ import annotations

import argparse

from .experiments import run_hybrid_search_experiment


def main(argv: list[str] | None = None) -> None:
    """CLI 메인 함수."""
    parser = argparse.ArgumentParser(
        description="ex08 step3 — 하이브리드 검색 실험",
    )
    parser.add_argument(
        "--max-queries",
        type=int,
        default=None,
        help="실험에 사용할 최대 쿼리 수 (기본값: 전체)",
    )
    args = parser.parse_args(argv)
    run_hybrid_search_experiment(max_queries=args.max_queries)


if __name__ == "__main__":
    main()
