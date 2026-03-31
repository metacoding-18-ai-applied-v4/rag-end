"""step3 — RAG 평가 지표 계산 함수."""


def calculate_precision_at_k(
    retrieved_sources: list[str],
    relevant_sources: list[str],
    k: int,
) -> float:
    """Precision@K: 상위 K개 결과 중 관련 문서 비율."""
    top_k = retrieved_sources[:k]
    relevant_set = set(relevant_sources)
    hits = sum(1 for src in top_k if any(rel in src for rel in relevant_set))
    return hits / k if k > 0 else 0.0


def calculate_recall_at_k(
    retrieved_sources: list[str],
    relevant_sources: list[str],
    k: int,
) -> float:
    """Recall@K: 관련 문서 중 상위 K개에 포함된 비율."""
    top_k = retrieved_sources[:k]
    relevant_set = set(relevant_sources)
    hits = sum(1 for rel in relevant_set if any(rel in src for src in top_k))
    return hits / len(relevant_set) if relevant_set else 0.0


def estimate_hallucination_rate(
    answers: list[str],
    contexts: list[list[str]],
) -> float:
    """답변이 컨텍스트에 근거하지 않는 비율을 추정한다.

    핵심 단어(4자 이상)의 컨텍스트 등장 비율이 30% 미만이면 환각으로 판정.
    """
    hallucination_count = 0

    for answer, context_docs in zip(answers, contexts):
        context_combined = " ".join(context_docs).lower()
        key_words = [w for w in answer.lower().split() if len(w) > 3]

        if key_words:
            context_words = set(context_combined.split())
            overlap = len([w for w in key_words if w in context_words]) / len(key_words)
            if overlap < 0.3:
                hallucination_count += 1

    return hallucination_count / len(answers) if answers else 0.0


def calculate_mrr(
    retrieved_sources_list: list[list[str]],
    relevant_sources_list: list[list[str]],
) -> float:
    """Mean Reciprocal Rank: 첫 번째 관련 문서의 순위 역수 평균.

    각 질문에 대해 검색된 문서 목록에서 첫 번째 관련 문서가 나타나는
    위치의 역수를 계산하고, 전체 질문에 대해 평균을 낸다.
    """
    reciprocal_ranks = []

    for retrieved, relevant in zip(retrieved_sources_list, relevant_sources_list):
        relevant_set = set(relevant)
        rr = 0.0

        for rank, src in enumerate(retrieved, 1):
            if any(rel in src for rel in relevant_set):
                rr = 1.0 / rank
                break

        reciprocal_ranks.append(rr)

    return sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0
