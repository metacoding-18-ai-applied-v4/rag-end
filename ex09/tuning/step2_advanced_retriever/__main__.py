"""step2_advanced_retriever CLI.

사용법:
    python -m ex09.tuning.step2_advanced_retriever                     # 전체 실행
    python -m ex09.tuning.step2_advanced_retriever --step 2-1          # ParentDoc만
    python -m ex09.tuning.step2_advanced_retriever --step 2-2          # Compression만
    python -m ex09.tuning.step2_advanced_retriever --step 2-3          # SelfQuery만
    python -m ex09.tuning.step2_advanced_retriever --query "보안 위반"  # 커스텀 쿼리
    python -m ex09.tuning.step2_advanced_retriever --top_k 3           # top_k 변경
"""

from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv

load_dotenv()

from .experiments import (
    _load_embeddings,
    run_parent_doc_experiment,
    run_self_query_experiment,
    run_compression_experiment,
    run_all,
)

from rich.console import Console

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(description="ex09 step2: 고급 Retriever 실험")
    parser.add_argument(
        "--step",
        choices=["2-1", "2-2", "2-3"],
        default=None,
        help="실행할 실험 (미지정 시 전체)",
    )
    parser.add_argument("--query", type=str, default=None, help="검색 쿼리")
    parser.add_argument("--top_k", type=int, default=2, help="검색 결과 수 (기본: 2)")
    args = parser.parse_args()

    if args.step is None:
        run_all(query=args.query, top_k=args.top_k)
        return

    embeddings = _load_embeddings()

    if args.step == "2-1":
        console.print("[bold]실험 2-1: ParentDocumentRetriever[/bold]")
        run_parent_doc_experiment(args.query, top_k=args.top_k, embeddings=embeddings)
    elif args.step == "2-2":
        console.print("[bold]실험 2-2: ContextualCompressionRetriever[/bold]")
        run_compression_experiment(args.query, top_k=args.top_k, embeddings=embeddings)
    elif args.step == "2-3":
        console.print("[bold]실험 2-3: SelfQueryRetriever[/bold]")
        run_self_query_experiment(args.query, top_k=args.top_k, embeddings=embeddings)


if __name__ == "__main__":
    main()
