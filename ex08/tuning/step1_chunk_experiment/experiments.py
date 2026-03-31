"""실험 실행기 — step 1-1 ~ 1-5.

step 1-1  청크 크기 실험 (300 / 500 / 1000자)
step 1-2  오버랩 비율 실험 (10% / 20% / 30%)
step 1-3  청킹 전략 비교 (Fixed vs Recursive vs Semantic) — 긴 문서
step 1-4  짧은 문서 실험
step 1-5  Retriever 파라미터 튜닝 (k / threshold / metadata)
"""

from __future__ import annotations

import time

from rich.console import Console

from .analysis import analyze_chunks
from .data import SAMPLE_DOCUMENT, SAMPLE_DOCUMENTS, SHORT_DOCUMENT, TEST_QUERIES
from .display import print_experiment_table
from .retriever import InMemoryRetriever, run_k_value_experiment, run_metadata_filter_experiment, run_threshold_experiment
from .strategies import fixed_size_chunking, recursive_character_chunking, semantic_chunking

console = Console()


# ── step 1-1: 청크 크기 실험 ─────────────────────────────────────
def run_chunk_size_experiment(percentile: int = 70) -> None:
    """청크 크기(300 / 500 / 1000자) 별 결과를 비교합니다."""
    console.print("[bold]step 1-1: 청크 크기 실험[/bold]")

    text = SAMPLE_DOCUMENT
    console.print(f"[green]샘플 문서 로드:[/green] {len(text)}자")

    results = []
    chunk_sizes = [300, 500, 1000]

    for size in chunk_sizes:
        overlap = size // 10
        start = time.time()
        chunks = fixed_size_chunking(text, chunk_size=size, overlap=overlap)
        elapsed = time.time() - start

        stats = analyze_chunks(chunks)
        results.append(
            {
                "전략": f"Fixed-size ({size}자)",
                "청크 수": stats["count"],
                "평균 크기": f"{stats['avg_size']:.0f}자",
                "최소 크기": f"{stats['min_size']}자",
                "최대 크기": f"{stats['max_size']}자",
                "실행 시간": f"{elapsed:.3f}s",
            }
        )

    print_experiment_table("청크 크기별 비교", results)


# ── step 1-2: 오버랩 비율 실험 ───────────────────────────────────
def run_overlap_experiment() -> None:
    """오버랩 비율(10% / 20% / 30%) 별 결과를 비교합니다."""
    console.print("[bold]step 1-2: 오버랩 비율 실험[/bold]")

    text = SAMPLE_DOCUMENT
    chunk_size = 500
    overlap_ratios = [0.1, 0.2, 0.3]
    results = []

    for ratio in overlap_ratios:
        overlap = int(chunk_size * ratio)
        chunks = fixed_size_chunking(text, chunk_size=chunk_size, overlap=overlap)
        stats = analyze_chunks(chunks)
        results.append(
            {
                "오버랩 비율": f"{int(ratio * 100)}%",
                "오버랩 문자 수": f"{overlap}자",
                "청크 수": stats["count"],
                "평균 크기": f"{stats['avg_size']:.0f}자",
            }
        )

    print_experiment_table("오버랩 비율별 비교", results)


# ── step 1-3: 전략 비교 (긴 문서) ────────────────────────────────
def run_strategy_comparison(percentile: int = 70) -> None:
    """Fixed / Recursive / Semantic 전략을 긴 문서로 비교합니다."""
    console.print("[bold]step 1-3: 청킹 전략 비교 (긴 문서)[/bold]")

    text = SAMPLE_DOCUMENT
    console.print(f"[green]샘플 문서 로드:[/green] {len(text)}자")
    results = []

    # Fixed-size
    start = time.time()
    fixed = fixed_size_chunking(text, chunk_size=500, overlap=50)
    stats = analyze_chunks(fixed)
    results.append(
        {
            "전략": "Fixed-size (500자)",
            "청크 수": stats["count"],
            "평균 크기": f"{stats['avg_size']:.0f}자",
            "실행 시간": f"{time.time() - start:.3f}s",
            "특징": "균일한 크기, 빠른 처리",
        }
    )

    # Recursive
    start = time.time()
    recursive = recursive_character_chunking(text, chunk_size=500, overlap=50)
    stats = analyze_chunks(recursive)
    results.append(
        {
            "전략": "Recursive Character",
            "청크 수": stats["count"],
            "평균 크기": f"{stats['avg_size']:.0f}자",
            "실행 시간": f"{time.time() - start:.3f}s",
            "특징": "문단/문장 경계 존중",
        }
    )

    # Semantic
    console.print("[dim]시맨틱 청킹 실험 중...[/dim]")
    start = time.time()
    semantic = semantic_chunking(text, percentile=percentile)
    stats = analyze_chunks(semantic)
    results.append(
        {
            "전략": f"Semantic (percentile={percentile})",
            "청크 수": stats["count"],
            "평균 크기": f"{stats['avg_size']:.0f}자",
            "실행 시간": f"{time.time() - start:.3f}s",
            "특징": "의미 단위 분할, 최고 품질",
        }
    )

    print_experiment_table("청킹 전략 비교", results)


# ── step 1-4: 짧은 문서 실험 ─────────────────────────────────────
def run_short_doc_experiment(percentile: int = 70) -> None:
    """짧은 문서에 각 전략을 적용했을 때 결과를 비교합니다."""
    console.print("[bold]step 1-4: 짧은 문서 실험[/bold]")

    text = SHORT_DOCUMENT
    console.print(f"[green]짧은 문서 로드:[/green] {len(text)}자")
    results = []

    fixed = fixed_size_chunking(text, chunk_size=500, overlap=50)
    stats = analyze_chunks(fixed)
    results.append({"전략": "Fixed-size (500자)", "청크 수": stats["count"], "평균 크기": f"{stats['avg_size']:.0f}자"})

    recursive = recursive_character_chunking(text, chunk_size=500, overlap=50)
    stats = analyze_chunks(recursive)
    results.append({"전략": "Recursive Character", "청크 수": stats["count"], "평균 크기": f"{stats['avg_size']:.0f}자"})

    semantic = semantic_chunking(text, percentile=percentile)
    stats = analyze_chunks(semantic)
    results.append({"전략": f"Semantic (percentile={percentile})", "청크 수": stats["count"], "평균 크기": f"{stats['avg_size']:.0f}자"})

    print_experiment_table("짧은 문서 청킹 비교", results)

    console.print(
        "\n[bold]관찰:[/bold] 짧은 문서는 청크 수 1로 수렴 → "
        "청킹 전략보다 문서 단위 관리가 중요합니다."
    )


# ── step 1-5: Retriever 파라미터 실험 ────────────────────────────
def run_retriever_experiment(
    k: int = 5,
    threshold: float = 0.2,
    department: str | None = None,
) -> None:
    """k값 / threshold / metadata filter 를 실험합니다."""
    console.print("[bold]step 1-5: Retriever 파라미터 튜닝[/bold]")
    console.print("[cyan]인메모리 샘플 데이터 모드로 실행합니다.[/cyan]")

    retriever = InMemoryRetriever(SAMPLE_DOCUMENTS)

    console.print(f"\n[bold yellow]1. k값 실험 (k=3, 5, 10)[/bold yellow]")
    k_results = run_k_value_experiment(retriever, TEST_QUERIES)
    print_experiment_table("k값별 검색 결과 비교", k_results)

    console.print(f"\n[bold yellow]2. Similarity Threshold 실험[/bold yellow]")
    th_results = run_threshold_experiment(retriever, TEST_QUERIES)
    print_experiment_table("Threshold별 검색 결과 비교", th_results)

    console.print(f"\n[bold yellow]3. Metadata Filtering 실험[/bold yellow]")
    filter_query = "복리후생 규정 안내"
    console.print(f"  테스트 쿼리: '{filter_query}'")
    filter_results = run_metadata_filter_experiment(
        retriever, filter_query, department=department
    )
    print_experiment_table("메타데이터 필터별 검색 결과", filter_results)

    console.print(
        f"\n[bold]권장 Retriever 설정:[/bold]\n"
        f"  - k={k} (일반적인 RAG 최적값)\n"
        f"  - threshold={threshold} (저품질 문서 필터링)\n"
        f"  - metadata filtering: 부서별/문서 유형별 필터 적용 권장"
    )
