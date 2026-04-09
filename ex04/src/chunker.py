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

    chunks = []                          # 결과를 담을 리스트
    step = chunk_size - overlap          # 다음 청크 시작 위치 (500-100=400자씩 이동)
    start = 0                           # 현재 위치

    while start < len(text):            # 텍스트 끝까지 반복
        end = start + chunk_size         # 현재 위치에서 500자 잘라내기
        chunk = text[start:end].strip()  # 앞뒤 공백 제거
        if chunk:                        # 빈 문자열이 아니면
            chunks.append(chunk)         # 결과에 추가
        start += step                    # 400자 뒤로 이동 (100자 겹침)

    return chunks
