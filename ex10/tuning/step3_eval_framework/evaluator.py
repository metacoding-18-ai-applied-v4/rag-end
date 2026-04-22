"""step3 — 평가 실행 로직.

strategies.STRATEGIES에서 꺼낸 조합으로 벡터DB를 빌드하고,
테스트 질문을 돌린 뒤 지표를 계산한다.
"""

from __future__ import annotations

import time

from .metrics import (
    calculate_mrr,
    calculate_precision_at_k,
    calculate_recall_at_k,
    estimate_hallucination_rate,
)
from ._eval_utils import (
    build_vectordb,
    generate_answer,
    load_test_questions,
)
from .strategies import STRATEGY_ORDER, Strategy, get_strategy


def run_evaluation(
    k: int = 3,
    strategy_name: str = "D",
    generate_answers: bool = False,
) -> dict:
    """한 조합으로 전체 평가 파이프라인을 실행한다.

    1. strategy 조회
    2. 해당 parser/chunker로 벡터DB 구축
    3. 각 질문마다 query_transform → retrieve → rerank
    4. Precision@k · Recall@k · MRR · Hallucination · Latency 계산
    """
    strategy = get_strategy(strategy_name)

    # 1) 벡터DB 구축
    collection = build_vectordb(strategy.parse_fn, strategy.chunk_fn)
    doc_count = collection.count()

    # 2) 테스트 질문 로드
    questions = load_test_questions()
    if not questions:
        return {
            "strategy": strategy_name,
            "error": "test_questions.json이 없거나 비어 있습니다.",
        }

    all_retrieved_sources: list[list[str]] = []
    all_relevant_sources: list[list[str]] = []
    all_answers: list[str] = []
    all_contexts: list[list[str]] = []
    question_results: list[dict] = []

    total_start = time.time()

    for q in questions:
        query_raw = q["query"]
        relevant = q.get("relevant_sources", [])

        # 3a) query transform
        query = strategy.query_transform_fn(query_raw)

        # 3b) 검색 (리랭크를 쓸 경우 넉넉히 뽑아 후처리)
        fetch_k = k * 3 if strategy.uses_rerank else k
        retrieved = strategy.retrieve_fn(collection, query, fetch_k)

        # 3c) 리랭크 + top-k 컷
        retrieved = strategy.rerank_fn(query, retrieved)[:k]
        retrieved_sources = [r["source"] for r in retrieved]

        # 답변 수집 (generate_answers=False면 expected_answer를 답변으로 간주)
        context_docs = [r["text"] for r in retrieved]
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
            "query": query_raw,
            "query_transformed": query,
            "category": q.get("category", ""),
            "relevant_sources": relevant,
            "retrieved_sources": retrieved_sources,
            "precision_at_k": round(precision, 3),
            "recall_at_k": round(recall, 3),
            "answer": answer[:200],
        })

    total_elapsed = time.time() - total_start
    latency_per_query_ms = (total_elapsed / max(len(questions), 1)) * 1000

    # 4) 전체 지표 집계
    avg_precision = sum(r["precision_at_k"] for r in question_results) / len(question_results)
    avg_recall = sum(r["recall_at_k"] for r in question_results) / len(question_results)
    mrr = calculate_mrr(all_retrieved_sources, all_relevant_sources)
    hallucination = estimate_hallucination_rate(all_answers, all_contexts)

    # 카테고리별 집계
    category_stats: dict[str, dict] = {}
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
        "strategy": strategy_name,
        "strategy_label": strategy.name,
        "strategy_description": strategy.description,
        "summary": {
            "total_questions": len(questions),
            "k": k,
            "document_count": doc_count,
            "avg_precision_at_k": round(avg_precision, 3),
            "avg_recall_at_k": round(avg_recall, 3),
            "mrr": round(mrr, 3),
            "hallucination_rate": round(hallucination, 3),
            "latency_ms_per_query": round(latency_per_query_ms, 1),
            "total_seconds": round(total_elapsed, 2),
        },
        "category_stats": category_stats,
        "question_results": question_results,
    }


def run_all_strategies(k: int = 3, generate_answers: bool = False) -> dict[str, dict]:
    """A/B/C/D 네 조합을 차례로 돌려 묶어 돌려준다."""
    results: dict[str, dict] = {}
    for name in STRATEGY_ORDER:
        results[name] = run_evaluation(k=k, strategy_name=name, generate_answers=generate_answers)
    return results
