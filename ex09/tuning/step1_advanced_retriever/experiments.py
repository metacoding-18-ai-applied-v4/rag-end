"""step1 실험 실행기 -- 1-1 ParentDoc / 1-2 SelfQuery / 1-3 Compression."""

from __future__ import annotations

import os
import sys
from typing import Any

from rich.console import Console

from .data import PARENT_DOCUMENTS, CHILD_CHUNKS, TOPIC_KEYWORDS, TEST_QUERIES
from .retrievers import (
    ParentDocumentRetriever,
    SelfQueryRetriever,
    ContextualCompressionRetriever,
)
from .display import (
    show_parent_doc_results,
    show_self_query_results,
    show_compression_results,
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


def _build_flat_documents() -> list[dict]:
    """자식 청크를 평면 문서 리스트로 변환합니다."""
    return [
        {
            "content": chunk["content"],
            "metadata": {"parent_id": chunk["parent_id"]},
        }
        for chunk in CHILD_CHUNKS
    ]


# ---------------------------------------------------------------------------
# 개별 실험
# ---------------------------------------------------------------------------

def run_parent_doc_experiment(
    query: str | None = None,
    top_k: int = 2,
    embeddings: Any | None = None,
) -> list[dict]:
    """실험 1-1: ParentDocumentRetriever."""
    query = query or TEST_QUERIES[0]
    retriever = ParentDocumentRetriever(PARENT_DOCUMENTS, CHILD_CHUNKS, embeddings)
    results = retriever.search(query, top_k=top_k)
    show_parent_doc_results(results, query)
    return results


def run_self_query_experiment(
    query: str | None = None,
    top_k: int = 3,
    embeddings: Any | None = None,
) -> list[dict]:
    """실험 1-2: SelfQueryRetriever."""
    query = query or TEST_QUERIES[1]
    # 부모 문서를 SelfQuery 대상 문서로 사용
    docs = [
        {
            "content": doc["content"],
            "metadata": doc["metadata"],
        }
        for doc in PARENT_DOCUMENTS
    ]
    retriever = SelfQueryRetriever(docs, TOPIC_KEYWORDS, embeddings)
    results = retriever.search(query, top_k=top_k)
    show_self_query_results(results, query)
    return results


def run_compression_experiment(
    query: str | None = None,
    top_k: int = 3,
    embeddings: Any | None = None,
) -> list[dict]:
    """실험 1-3: ContextualCompressionRetriever."""
    query = query or TEST_QUERIES[0]
    docs = [
        {
            "content": doc["content"],
            "metadata": doc["metadata"],
        }
        for doc in PARENT_DOCUMENTS
    ]
    retriever = ContextualCompressionRetriever(docs, embeddings)
    results = retriever.search(query, top_k=top_k)
    show_compression_results(results, query)
    return results


# ---------------------------------------------------------------------------
# 전체 실행
# ---------------------------------------------------------------------------

def run_all(query: str | None = None, top_k: int = 2) -> None:
    """실험 1-1 ~ 1-3 을 모두 실행합니다."""
    console.print("[bold]ex09 step1: 고급 Retriever 실험[/bold]")

    embeddings = _load_embeddings()

    run_parent_doc_experiment(query, top_k=top_k, embeddings=embeddings)
    run_self_query_experiment(query, top_k=top_k, embeddings=embeddings)
    run_compression_experiment(query, top_k=top_k, embeddings=embeddings)

    show_summary()
