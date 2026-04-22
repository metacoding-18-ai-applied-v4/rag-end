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
    # TODO: ArgumentParser를 생성하고 --max-queries (int, default=None) 인자를 추가합니다.
    #       args를 파싱한 뒤 run_hybrid_search_experiment(max_queries=args.max_queries)를 호출합니다.
    parser = argparse.ArgumentParser(
        description="ex08 step3 — 하이브리드 검색 실험",
    )
    parser.add_argument(
        "--max-queries",
        type=int,
        default=None,
        help="실험에 사용할 최대 쿼리 수 (기본값: 전체)",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.5,
        help="Vector 가중치 (0.0=BM25만, 1.0=Vector만, 기본값: 0.5)",
    )
    args = parser.parse_args(argv)
    run_hybrid_search_experiment(max_queries=args.max_queries, alpha=args.alpha)


if __name__ == "__main__":
    main()
