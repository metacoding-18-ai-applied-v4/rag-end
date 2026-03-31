"""step3 — 평가 실행 로직.

벡터DB를 구축하고, 테스트 질문으로 검색을 수행한 뒤, 평가 지표를 계산한다.
"""

import json
import os
from pathlib import Path

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

from .metrics import (
    calculate_mrr,
    calculate_precision_at_k,
    calculate_recall_at_k,
    estimate_hallucination_rate,
)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")


# ---------------------------------------------------------------------------
# 벡터DB 구축
# ---------------------------------------------------------------------------

def build_vectordb(collection_name: str = "eval_documents") -> chromadb.Collection:
    """data/docs 폴더의 문서를 파싱하여 ChromaDB 컬렉션에 저장한다."""
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )

    # 기존 컬렉션이 있으면 삭제 후 재생성
    try:
        client.delete_collection(collection_name)
    except (ValueError, Exception):
        pass

    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    # data/docs 폴더에서 문서 텍스트 수집
    docs_dir = DATA_DIR / "docs"
    if not docs_dir.exists():
        return collection

    ids = []
    documents = []
    metadatas = []

    for doc_path in sorted(docs_dir.iterdir()):
        if doc_path.suffix.lower() == ".pdf":
            pages = _extract_pdf_text(doc_path)
            for page_num, text in enumerate(pages, 1):
                if text.strip():
                    doc_id = f"{doc_path.stem}_p{page_num}"
                    ids.append(doc_id)
                    documents.append(text[:5000])
                    metadatas.append({
                        "source": doc_path.stem,
                        "page": str(page_num),
                        "format": "pdf",
                    })

    if ids:
        collection.add(ids=ids, documents=documents, metadatas=metadatas)

    return collection


def _extract_pdf_text(pdf_path: Path) -> list[str]:
    """PDF에서 페이지별 텍스트를 추출한다."""
    try:
        import fitz

        doc = fitz.open(str(pdf_path))
        pages = [doc[i].get_text() for i in range(len(doc))]
        doc.close()
        return pages
    except ImportError:
        return []


# ---------------------------------------------------------------------------
# 검색 수행
# ---------------------------------------------------------------------------

def search_collection(
    collection: chromadb.Collection,
    query: str,
    k: int = 5,
) -> dict:
    """컬렉션에서 질문에 대해 상위 K개 결과를 검색한다."""
    results = collection.query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []
    for i in range(len(results["ids"][0])):
        retrieved.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "source": results["metadatas"][0][i].get("source", ""),
            "page": results["metadatas"][0][i].get("page", ""),
            "distance": results["distances"][0][i],
        })

    return {
        "query": query,
        "retrieved": retrieved,
        "sources": [r["source"] for r in retrieved],
    }


# ---------------------------------------------------------------------------
# LLM 답변 생성
# ---------------------------------------------------------------------------

def generate_answer(query: str, context_docs: list[str]) -> str:
    """검색된 컨텍스트를 기반으로 LLM 답변을 생성한다."""
    try:
        import httpx

        context = "\n\n---\n\n".join(context_docs[:3])
        prompt = (
            f"다음 문서 내용을 참고하여 질문에 답하세요.\n\n"
            f"[문서]\n{context}\n\n"
            f"[질문]\n{query}\n\n"
            f"[답변]"
        )

        resp = httpx.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        return f"[답변 생성 실패: {str(e)[:80]}]"


# ---------------------------------------------------------------------------
# 평가 실행
# ---------------------------------------------------------------------------

def load_test_questions() -> list[dict]:
    """test_questions.json을 로드한다."""
    questions_path = DATA_DIR / "test_questions.json"
    if not questions_path.exists():
        return []

    with open(questions_path, encoding="utf-8") as f:
        data = json.load(f)

    return data.get("questions", [])


def run_evaluation(k: int = 3, generate_answers: bool = False) -> dict:
    """전체 평가 파이프라인을 실행한다.

    1. 벡터DB 구축
    2. 테스트 질문 로드
    3. 각 질문에 대해 검색 수행
    4. 평가 지표 계산
    """
    # 1) 벡터DB 구축
    collection = build_vectordb()
    doc_count = collection.count()

    # 2) 테스트 질문 로드
    questions = load_test_questions()
    if not questions:
        return {"error": "test_questions.json이 없거나 비어 있습니다."}

    # 3) 검색 + 평가
    all_retrieved_sources = []
    all_relevant_sources = []
    all_answers = []
    all_contexts = []
    question_results = []

    for q in questions:
        query = q["query"]
        relevant = q.get("relevant_sources", [])

        search_result = search_collection(collection, query, k=k)
        retrieved_sources = search_result["sources"]

        # 답변 생성 (옵션)
        context_docs = [r["text"] for r in search_result["retrieved"]]
        if generate_answers:
            answer = generate_answer(query, context_docs)
        else:
            answer = q.get("expected_answer", "")

        precision = calculate_precision_at_k(retrieved_sources, relevant, k)
        recall = calculate_recall_at_k(retrieved_sources, relevant, k)

        all_retrieved_sources.append(retrieved_sources)
        all_relevant_sources.append(relevant)
        all_answers.append(answer)
        all_contexts.append(context_docs)

        question_results.append({
            "id": q.get("id", 0),
            "query": query,
            "category": q.get("category", ""),
            "relevant_sources": relevant,
            "retrieved_sources": retrieved_sources,
            "precision_at_k": round(precision, 3),
            "recall_at_k": round(recall, 3),
            "answer": answer[:200],
        })

    # 4) 전체 지표 집계
    avg_precision = sum(r["precision_at_k"] for r in question_results) / len(question_results)
    avg_recall = sum(r["recall_at_k"] for r in question_results) / len(question_results)
    mrr = calculate_mrr(all_retrieved_sources, all_relevant_sources)
    hallucination = estimate_hallucination_rate(all_answers, all_contexts)

    # 카테고리별 집계
    category_stats = {}
    for r in question_results:
        cat = r["category"] or "기타"
        if cat not in category_stats:
            category_stats[cat] = {"precision": [], "recall": [], "count": 0}
        category_stats[cat]["precision"].append(r["precision_at_k"])
        category_stats[cat]["recall"].append(r["recall_at_k"])
        category_stats[cat]["count"] += 1

    for cat, stats in category_stats.items():
        stats["avg_precision"] = round(sum(stats["precision"]) / len(stats["precision"]), 3)
        stats["avg_recall"] = round(sum(stats["recall"]) / len(stats["recall"]), 3)
        del stats["precision"]
        del stats["recall"]

    return {
        "summary": {
            "total_questions": len(questions),
            "k": k,
            "document_count": doc_count,
            "avg_precision_at_k": round(avg_precision, 3),
            "avg_recall_at_k": round(avg_recall, 3),
            "mrr": round(mrr, 3),
            "hallucination_rate": round(hallucination, 3),
        },
        "category_stats": category_stats,
        "question_results": question_results,
    }
