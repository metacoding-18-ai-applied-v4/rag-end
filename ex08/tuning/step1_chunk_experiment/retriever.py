"""Retriever 파라미터 튜닝 — k값, threshold, metadata filter 실험."""

from __future__ import annotations

import os
from pathlib import Path

from rich.console import Console

console = Console()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask")
USE_SAMPLE_DATA = os.getenv("USE_SAMPLE_DATA", "true").lower() == "true"
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # ex08/
CHROMA_PERSIST_DIR = os.getenv(
    "CHROMA_PERSIST_DIR", str(BASE_DIR / "data" / "chroma_db")
)


# ── InMemoryRetriever ────────────────────────────────────────────
class InMemoryRetriever:
    """인메모리 샘플 데이터를 사용하는 검색기."""

    def __init__(self, documents: list[dict]):
        self.documents = documents

    @staticmethod
    def similarity_score(query: str, doc_content: str) -> float:
        """쿼리-문서 간 단순 키워드 유사도를 계산합니다."""
        query_words = set(query.lower().split())
        doc_words = set(doc_content.lower().split())
        if not query_words:
            return 0.0
        return len(query_words & doc_words) / len(query_words)

    def search(
        self,
        query: str,
        k: int = 5,
        threshold: float = 0.0,
        metadata_filter: dict | None = None,
    ) -> list[dict]:
        """문서를 검색합니다."""
        candidates = self.documents
        if metadata_filter:
            candidates = [
                doc
                for doc in candidates
                if all(
                    doc["metadata"].get(fk) == fv
                    for fk, fv in metadata_filter.items()
                )
            ]

        scored_docs = []
        for doc in candidates:
            score = self.similarity_score(query, doc["content"])
            if score >= threshold:
                scored_docs.append(
                    {
                        "score": score,
                        "content": doc["content"],
                        "metadata": doc["metadata"],
                        "id": doc["id"],
                    }
                )

        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        return scored_docs[:k]


# ── ChromaDB 기반 검색기 팩토리 ──────────────────────────────────
def create_chroma_retriever(k: int = 5):
    """ChromaDB 기반 검색기를 생성합니다. 실패 시 None 을 반환합니다."""
    chroma_path = Path(CHROMA_PERSIST_DIR)
    if not chroma_path.exists():
        console.print(
            "[yellow]ChromaDB 경로가 없습니다. 인메모리 샘플 모드를 사용합니다.[/yellow]"
        )
        return None

    try:
        from langchain_chroma import Chroma
        from langchain_community.embeddings import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
        )
        vectorstore = Chroma(
            persist_directory=str(chroma_path),
            embedding_function=embeddings,
        )
        return vectorstore.as_retriever(search_kwargs={"k": k})

    except Exception as e:
        console.print(f"[red]ChromaDB 로드 실패: {e}[/red]")
        console.print("[yellow]인메모리 샘플 모드로 전환합니다.[/yellow]")
        return None


# ── k값 실험 ─────────────────────────────────────────────────────
def run_k_value_experiment(
    retriever: InMemoryRetriever, test_queries: list[str]
) -> list[dict]:
    """k 값(3, 5, 10) 에 따른 검색 결과를 비교합니다."""
    results = []
    k_values = [3, 5, 10]
    recommendations = {
        3: "정확도 중시, 컨텍스트 창 절약",
        5: "일반적인 RAG 최적값 (권장)",
        10: "높은 재현율 필요, ReRanker와 함께 사용",
    }

    for k in k_values:
        avg_count = 0
        avg_top = 0.0
        for query in test_queries:
            docs = retriever.search(query, k=k)
            avg_count += len(docs)
            if docs:
                avg_top += docs[0]["score"]
        avg_count /= len(test_queries)
        avg_top /= len(test_queries)

        results.append(
            {
                "k값": k,
                "평균 반환 문서 수": f"{avg_count:.1f}",
                "평균 최고 점수": f"{avg_top:.3f}",
                "추천 상황": recommendations.get(k, ""),
            }
        )

    return results


# ── threshold 실험 ───────────────────────────────────────────────
def run_threshold_experiment(
    retriever: InMemoryRetriever, test_queries: list[str]
) -> list[dict]:
    """similarity threshold 별 필터링 효과를 비교합니다."""
    results = []
    thresholds = [0.0, 0.1, 0.2, 0.3, 0.5]

    for th in thresholds:
        total_returned = 0
        total_filtered = 0
        for query in test_queries:
            docs_all = retriever.search(query, k=10, threshold=0.0)
            docs_th = retriever.search(query, k=10, threshold=th)
            total_returned += len(docs_th)
            total_filtered += len(docs_all) - len(docs_th)
        avg_returned = total_returned / len(test_queries)
        avg_filtered = total_filtered / len(test_queries)

        results.append(
            {
                "임계값": th,
                "평균 반환 수": f"{avg_returned:.1f}",
                "평균 필터링 수": f"{avg_filtered:.1f}",
                "효과": "높을수록 저품질 문서 제거",
            }
        )

    return results


# ── metadata filter 실험 ─────────────────────────────────────────
def run_metadata_filter_experiment(
    retriever: InMemoryRetriever, query: str, department: str | None = None
) -> list[dict]:
    """메타데이터 필터 조건별 검색 결과를 비교합니다."""
    filter_configs: list[tuple[dict | None, str]] = [
        (None, "필터 없음 (전체)"),
        ({"department": "HR"}, "부서: HR"),
        ({"department": "FINANCE"}, "부서: FINANCE"),
        ({"department": "IT"}, "부서: IT"),
        ({"version": "v1.0"}, "버전: v1.0"),
        ({"doc_type": "policy"}, "문서 유형: 정책"),
        ({"doc_type": "benefit"}, "문서 유형: 복리후생"),
    ]

    # CLI 에서 --department 가 전달되면 해당 부서만 실험
    if department:
        filter_configs = [
            (None, "필터 없음 (전체)"),
            ({"department": department}, f"부서: {department}"),
        ]

    results = []
    for metadata_filter, description in filter_configs:
        docs = retriever.search(query, k=5, metadata_filter=metadata_filter)
        sources = [doc["metadata"].get("source", "알 수 없음") for doc in docs]
        results.append(
            {
                "필터 조건": description,
                "반환 문서 수": len(docs),
                "검색된 소스": ", ".join(sources) if sources else "없음",
            }
        )

    return results
