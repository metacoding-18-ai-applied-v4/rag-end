"""실험 실행기 — alpha 파라미터 실험 및 하이브리드 검색 데모."""

from __future__ import annotations

from rich.table import Table

from .data import SAMPLE_DOCUMENTS, SAMPLE_METADATAS
from .display import console, print_hybrid_demo
from .retrievers import BM25Retriever, EnsembleRetriever, VectorRetriever


# ── alpha 실험 ───────────────────────────────────────────────────
def run_alpha_experiment(
    bm25: BM25Retriever,
    vector: VectorRetriever,
    test_queries: list[str],
) -> list[dict]:
    """alpha 파라미터(0.0 ~ 1.0) 별 검색 결과를 비교합니다."""
    results = []
    alphas = [0.0, 0.3, 0.5, 0.7, 1.0]

    for alpha in alphas:
        ensemble = EnsembleRetriever(bm25, vector, alpha=alpha)
        total = sum(len(ensemble.search(q, top_k=5)) for q in test_queries)
        avg = total / len(test_queries)

        label = (
            "BM25만" if alpha == 0.0 else ("Vector만" if alpha == 1.0 else "혼합")
        )
        results.append(
            {
                "alpha": f"{alpha:.1f}",
                "구성": label,
                "BM25 가중치": f"{(1 - alpha) * 100:.0f}%",
                "Vector 가중치": f"{alpha * 100:.0f}%",
                "평균 반환 수": f"{avg:.1f}",
                "추천": (
                    "단어 정확히 일치"
                    if alpha == 0.0
                    else ("의미 유사도" if alpha == 1.0 else "균형 검색")
                ),
            }
        )

    return results


# ── 메인 실험 ────────────────────────────────────────────────────
def run_hybrid_search_experiment(*, max_queries: int | None = None) -> None:
    """하이브리드 검색 전체 실험을 실행합니다."""
    console.print("[bold]ex08 step3: 하이브리드 검색 실험[/bold]")

    console.print("[cyan]BM25 검색기 초기화 중...[/cyan]")
    bm25_retriever = BM25Retriever(SAMPLE_DOCUMENTS, SAMPLE_METADATAS)
    console.print("[green]BM25 검색기 준비 완료[/green]")

    console.print("[cyan]Vector 검색기 초기화 중...[/cyan]")
    vector_retriever = VectorRetriever(SAMPLE_DOCUMENTS, SAMPLE_METADATAS)

    console.print(
        "\n[bold yellow]1. alpha 파라미터 실험 (BM25:Vector 가중치 비율)[/bold yellow]"
    )
    test_queries = [
        "연차 신청 절차",
        "재택근무 조건",
        "출장비 정산 방법",
    ]

    if max_queries is not None:
        test_queries = test_queries[:max_queries]

    alpha_results = run_alpha_experiment(bm25_retriever, vector_retriever, test_queries)

    table = Table(title="alpha 파라미터별 비교")
    for col in alpha_results[0].keys():
        table.add_column(col, style="cyan")
    for row in alpha_results:
        table.add_row(*[str(v) for v in row.values()])
    console.print(table)

    console.print(
        "\n[bold yellow]2. 하이브리드 검색 데모 (alpha=0.5)[/bold yellow]"
    )
    demo_query = "연차 신청 절차와 승인 방법"
    console.print(f"  쿼리: '{demo_query}'")

    ensemble = EnsembleRetriever(bm25_retriever, vector_retriever, alpha=0.5)
    print_hybrid_demo(ensemble, demo_query)

    console.print(
        "\n[bold]하이브리드 검색 권장 설정:[/bold]\n"
        "  - 일반 질문 (의미 검색 중심): alpha=0.7\n"
        "  - 정확한 키워드 검색: alpha=0.3\n"
        "  - 균형 잡힌 기본값: alpha=0.5\n"
        "  - 한국어 특수용어/약어: alpha=0.3 (BM25 비중 높임)"
    )
