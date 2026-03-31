"""step2 실험 실행기 -- 2-1 약어확장 / 2-2 HyDE / 2-3 Multi-Query."""

from __future__ import annotations

import os
from typing import Any

from rich.console import Console

from .data import SEARCH_DOCUMENTS
from .rewriters import (
    expand_abbreviations,
    compare_hyde_vs_direct,
    generate_multi_queries,
    search_multi_query,
)
from .display import (
    show_abbreviation_results,
    show_hyde_results,
    show_multi_query_results,
    show_summary,
)

console = Console()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask")


def _load_embeddings() -> Any | None:
    """임베딩 모델을 로드합니다. 실패 시 None을 반환합니다."""
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings

        console.print(f"[dim]임베딩 모델 로드 중: {EMBEDDING_MODEL}[/dim]")
        emb = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
        )
        console.print("[green]임베딩 모델 로드 완료[/green]")
        return emb
    except Exception as exc:
        console.print(f"[yellow]임베딩 로드 실패 ({exc}), 키워드 폴백 모드[/yellow]")
        return None


# ---------------------------------------------------------------------------
# 개별 실험
# ---------------------------------------------------------------------------

def run_abbreviation_experiment(
    queries: list[str] | None = None,
) -> list[dict]:
    """실험 2-1: 약어/동의어 확장."""
    if queries is None:
        queries = [
            "WFH 정책이 어떻게 됩니까?",
            "OT 신청 절차를 알려주십시오",
            "PIP 대상자 기준은 무엇입니까?",
            "연차 신청 방법",
            "4대보험 가입 시기",
        ]

    results = [expand_abbreviations(q) for q in queries]
    show_abbreviation_results(results)
    return results


def run_hyde_experiment(
    query: str | None = None,
    embeddings: Any | None = None,
) -> dict:
    """실험 2-2: HyDE vs 직접 검색 비교."""
    query = query or "연차 신청 절차는 어떻게 됩니까?"
    result = compare_hyde_vs_direct(query, SEARCH_DOCUMENTS, embeddings)
    show_hyde_results(result)
    return result


def run_multi_query_experiment(
    query: str | None = None,
    num_queries: int = 3,
    embeddings: Any | None = None,
) -> dict:
    """실험 2-3: Multi-Query 생성 + 검색."""
    query = query or "재택근무 조건과 신청 방법"
    queries = generate_multi_queries(query, num_queries=num_queries)
    results = search_multi_query(queries, SEARCH_DOCUMENTS, embeddings, top_k=3)
    show_multi_query_results(query, queries, results)
    return {"queries": queries, "results": results}


# ---------------------------------------------------------------------------
# 전체 실행
# ---------------------------------------------------------------------------

def run_all(
    query: str | None = None,
    num_queries: int = 3,
) -> None:
    """실험 2-1 ~ 2-3 을 모두 실행합니다."""
    console.print("[bold]ex09 step2: Query Rewrite 실험[/bold]")

    embeddings = _load_embeddings()

    run_abbreviation_experiment()
    run_hyde_experiment(query=query, embeddings=embeddings)
    run_multi_query_experiment(query=query, num_queries=num_queries, embeddings=embeddings)

    show_summary()
