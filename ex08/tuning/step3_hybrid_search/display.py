"""Rich 테이블 출력 유틸리티."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from .retrievers import EnsembleRetriever

console = Console(force_terminal=True, width=100)


def print_hybrid_demo(ensemble: EnsembleRetriever, query: str) -> None:
    """하이브리드 검색 데모 결과를 출력합니다."""
    # TODO: ensemble.search(query, top_k=5)로 검색합니다.
    #       Table(title=f"하이브리드 검색 결과 (alpha={ensemble.alpha})")을 생성합니다.
    #       컬럼: 순위, BM25 점수, Vector 점수, Hybrid 점수, 내용 미리보기(50자+...)
    #       결과를 행으로 추가하고 console.print(table)로 출력합니다.
    results = ensemble.search(query, top_k=5)

    table = Table(title=f"하이브리드 검색 결과 (alpha={ensemble.alpha})")
    table.add_column("순위", style="cyan", justify="center")
    table.add_column("BM25 점수", style="yellow")
    table.add_column("Vector 점수", style="blue")
    table.add_column("Hybrid 점수", style="green")
    table.add_column("내용 미리보기", style="white")

    for rank, doc in enumerate(results, 1):
        table.add_row(
            str(rank),
            f"{doc.get('bm25_score', 0):.3f}",
            f"{doc.get('vector_score', 0):.3f}",
            f"{doc.get('hybrid_score', 0):.3f}",
            doc["content"][:50] + "...",
        )

    console.print(table)
