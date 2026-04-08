"""청킹 모듈 — 텍스트를 적당한 크기로 자르는 핵심 로직.

CH04 핵심: Fixed-size 청킹 (500자 + 100자 오버랩)
"""

from _chunk_utils import chunk_all_documents

# 기본 청킹 파라미터
DEFAULT_CHUNK_SIZE = 500
DEFAULT_OVERLAP = 100


def split_text_into_chunks(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    """텍스트 문자열을 Fixed-size 방식으로 청크 리스트로 분할합니다.

    오버랩을 적용하여 청크 경계 부근의 문맥 손실을 줄입니다.
    빈 텍스트나 공백만 있는 텍스트는 빈 리스트를 반환합니다.

    Args:
        text: 분할할 원본 텍스트 문자열
        chunk_size: 각 청크의 최대 문자 수 (기본: 500)
        overlap: 이전 청크와 겹치는 문자 수 (기본: 100)

    Returns:
        분할된 텍스트 청크 문자열 리스트

    Raises:
        ValueError: chunk_size가 overlap보다 작거나 같은 경우
    """
    if chunk_size <= overlap:
        raise ValueError(
            f"chunk_size({chunk_size})는 overlap({overlap})보다 커야 합니다."
        )

    text = text.strip()
    if not text:
        return []

    # TODO: chunk_size 단위로 텍스트를 자르되, overlap만큼 겹치게 합니다
    chunks = []
    step = chunk_size - overlap
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += step

    return chunks
