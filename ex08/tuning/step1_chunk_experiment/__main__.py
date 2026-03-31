"""step1_chunk_experiment CLI 진입점.

사용법:
    python -m tuning.step1_chunk_experiment --step 1-1
    python -m tuning.step1_chunk_experiment --step 1-3 --percentile 80
    python -m tuning.step1_chunk_experiment --step 1-5 --k 3 --threshold 0.3 --department HR
"""

from __future__ import annotations

import argparse
import sys

from .experiments import (
    run_chunk_size_experiment,
    run_overlap_experiment,
    run_retriever_experiment,
    run_short_doc_experiment,
    run_strategy_comparison,
)


STEP_CHOICES = ["1-1", "1-2", "1-3", "1-4", "1-5"]

STEP_DESCRIPTIONS = {
    "1-1": "청크 크기 실험 (300/500/1000자)",
    "1-2": "오버랩 비율 실험 (10%/20%/30%)",
    "1-3": "청킹 전략 비교 (Fixed vs Recursive vs Semantic)",
    "1-4": "짧은 문서 실험",
    "1-5": "Retriever 파라미터 튜닝 (k/threshold/metadata)",
}


def build_parser() -> argparse.ArgumentParser:
    """argparse 파서를 생성합니다."""
    parser = argparse.ArgumentParser(
        description="ex08 step1 — 청킹 전략 및 Retriever 파라미터 실험",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(
            f"  {step}: {desc}" for step, desc in STEP_DESCRIPTIONS.items()
        ),
    )
    parser.add_argument(
        "--step",
        choices=STEP_CHOICES,
        required=True,
        help="실행할 실험 단계 (1-1 ~ 1-5)",
    )
    parser.add_argument(
        "--percentile",
        type=int,
        default=70,
        help="시맨틱 청킹 백분위 임계값 (기본값: 70)",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Retriever top-k 값 (기본값: 5)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.2,
        help="Retriever similarity threshold (기본값: 0.2)",
    )
    parser.add_argument(
        "--department",
        type=str,
        default=None,
        help="Metadata filter 부서명 (예: HR, FINANCE, IT)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """CLI 메인 함수."""
    parser = build_parser()
    args = parser.parse_args(argv)

    dispatch = {
        "1-1": lambda: run_chunk_size_experiment(percentile=args.percentile),
        "1-2": lambda: run_overlap_experiment(),
        "1-3": lambda: run_strategy_comparison(percentile=args.percentile),
        "1-4": lambda: run_short_doc_experiment(percentile=args.percentile),
        "1-5": lambda: run_retriever_experiment(
            k=args.k, threshold=args.threshold, department=args.department
        ),
    }

    handler = dispatch.get(args.step)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    handler()


if __name__ == "__main__":
    main()
