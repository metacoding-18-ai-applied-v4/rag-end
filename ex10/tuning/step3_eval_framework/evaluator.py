"""step3 — 평가 실행 로직.

벡터DB를 구축하고, 테스트 질문으로 검색을 수행한 뒤, 평가 지표를 계산한다.
"""

from .metrics import (
    calculate_mrr,
    calculate_precision_at_k,
    calculate_recall_at_k,
    estimate_hallucination_rate,
)
from ._eval_utils import (
    build_vectordb,
    search_collection,
    generate_answer,
    load_test_questions,
)


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
