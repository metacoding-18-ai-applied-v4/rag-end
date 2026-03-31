"""통계 및 코사인 유사도 계산."""

from __future__ import annotations


def analyze_chunks(chunks: list[str]) -> dict:
    """청크 리스트의 기초 통계를 계산합니다.

    Returns:
        count, avg_size, min_size, max_size 키를 가진 딕셔너리.
    """
    # TODO: 빈 리스트이면 모든 값 0인 딕셔너리를 반환합니다.
    #       그 외에는 각 청크의 len()으로 count, avg_size, min_size, max_size를 계산합니다.
    if not chunks:
        return {"count": 0, "avg_size": 0, "min_size": 0, "max_size": 0}

    sizes = [len(c) for c in chunks]
    return {
        "count": len(chunks),
        "avg_size": sum(sizes) / len(sizes),
        "min_size": min(sizes),
        "max_size": max(sizes),
    }


def cosine_similarity(vec_a, vec_b) -> float:
    """두 벡터 간 코사인 유사도를 계산합니다.

    numpy 가 설치되어 있으면 사용하고, 없으면 순수 파이썬으로 계산합니다.
    """
    # TODO: numpy가 있으면 np.dot / (norm_a * norm_b)로 계산합니다.
    #       ImportError 시 순수 파이썬 내적/노름으로 계산합니다.
    #       분모가 0이면 0.0을 반환합니다.
    try:
        import numpy as np

        a = np.asarray(vec_a, dtype=float)
        b = np.asarray(vec_b, dtype=float)
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)

    except ImportError:
        dot = sum(x * y for x, y in zip(vec_a, vec_b))
        norm_a = sum(x * x for x in vec_a) ** 0.5
        norm_b = sum(x * x for x in vec_b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
