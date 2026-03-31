"""통계 및 코사인 유사도 계산."""

from __future__ import annotations


def analyze_chunks(chunks: list[str]) -> dict:
    """청크 리스트의 기초 통계를 계산합니다.

    Returns:
        count, avg_size, min_size, max_size 키를 가진 딕셔너리.
    """
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
