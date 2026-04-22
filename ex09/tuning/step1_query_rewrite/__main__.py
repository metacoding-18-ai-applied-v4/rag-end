"""step1_query_rewrite CLI.

사용법:
    python -m ex09.tuning.step1_query_rewrite                          # 전체 실행
    python -m ex09.tuning.step1_query_rewrite --step 1-1               # HyDE만
    python -m ex09.tuning.step1_query_rewrite --step 1-2               # Multi-Query만
    python -m ex09.tuning.step1_query_rewrite --step 1-3               # 약어확장만
    python -m ex09.tuning.step1_query_rewrite --query "WFH 신청 방법"   # 커스텀 쿼리
    python -m ex09.tuning.step1_query_rewrite --num_queries 5          # Multi-Query 수 변경
"""

from __future__ import annotations

import argparse

from dotenv import load_dotenv

load_dotenv()

from .experiments import (
    _load_embeddings,
    run_abbreviation_experiment,
    run_hyde_experiment,
    run_multi_query_experiment,
    run_all,
)

from rich.console import Console

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(description="ex09 step1: Query Rewrite 실험")
    parser.add_argument(
        "--step",
        choices=["1-1", "1-2", "1-3"],
        default=None,
        help="실행할 실험 (미지정 시 전체)",
    )
    parser.add_argument("--query", type=str, default=None, help="검색 쿼리")
    parser.add_argument("--num_queries", type=int, default=3, help="Multi-Query 생성 수 (기본: 3)")
    args = parser.parse_args()

    if args.step is None:
        run_all(query=args.query, num_queries=args.num_queries)
        return

    if args.step == "1-1":
        console.print("[bold]실험 1-1: HyDE[/bold]")
        embeddings = _load_embeddings()
        run_hyde_experiment(args.query, embeddings=embeddings)

    elif args.step == "1-2":
        console.print("[bold]실험 1-2: Multi-Query[/bold]")
        embeddings = _load_embeddings()
        run_multi_query_experiment(
            args.query, num_queries=args.num_queries, embeddings=embeddings,
        )

    elif args.step == "1-3":
        console.print("[bold]실험 1-3: 약어/동의어 확장[/bold]")
        queries = [args.query] if args.query else None
        run_abbreviation_experiment(queries)


if __name__ == "__main__":
    main()
