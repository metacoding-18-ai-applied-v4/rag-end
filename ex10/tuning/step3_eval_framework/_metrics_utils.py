"""step3 — 평가 지표 보조 함수 (완성 코드).

MRR 등 보조 지표 함수를 제공한다.
"""


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
