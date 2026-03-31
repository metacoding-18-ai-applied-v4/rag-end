"""
텍스트와 이미지 캡션을 청크(Chunk) 단위로 분할하는 모듈.

Fixed-size 청킹 방식을 사용하며 오버랩(overlap)으로
청크 경계에서 문맥 손실을 방지합니다.
각 청크에는 출처 추적을 위한 메타데이터가 부착됩니다.

청크 크기와 오버랩 설정:
- chunk_size: 500자 (기본)
- overlap: 100자 = 약 20% 오버랩
"""

import re
import sys
from pathlib import Path

# 기본 청킹 파라미터
DEFAULT_CHUNK_SIZE = 500
DEFAULT_OVERLAP = 100


# =====================================================================
# === INPUT ===
# extract_result: extractor.py의 반환 딕셔너리
# chunk_size: 청크 최대 문자 수 (기본 500)
# overlap: 청크 간 오버랩 문자 수 (기본 100)
# =====================================================================


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

    # === PROCESS ===
    chunks = []
    step = chunk_size - overlap  # 다음 청크 시작 위치 이동 단계
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += step

    # === OUTPUT ===
    return chunks


def build_text_chunk(
    chunk_text: str,
    doc_id: str,
    file_name: str,
    file_type: str,
    source_path: str,
    page: int,
    section: str = "",
    title: str = "",
    department: str = "",
    chunk_index: int = 0,
) -> dict:
    """텍스트 청크와 메타데이터를 결합한 청크 딕셔너리를 생성합니다.

    ChromaDB에 저장하기 위한 표준 형식으로 변환합니다.
    메타데이터는 나중에 출처 추적 및 필터링에 사용됩니다.

    Args:
        chunk_text: 청크 텍스트 내용
        doc_id: 문서 고유 ID (파일명 기반)
        file_name: 원본 파일명
        file_type: 파일 형식 (pdf/docx/xlsx)
        source_path: 원본 파일 절대 경로
        page: 출처 페이지 번호
        section: 섹션 또는 시트명 (선택)
        title: 문서 제목 (선택)
        department: 담당 부서 (선택)
        chunk_index: 문서 내 청크 순번

    Returns:
        {
            "id": 청크 고유 ID (str),
            "text": 청크 텍스트 (str),
            "metadata": {메타데이터 딕셔너리},
            "chunk_type": "text"
        }
    """
    chunk_id = f"{doc_id}_text_p{page:03d}_c{chunk_index:04d}"

    # === OUTPUT ===
    return {
        "id": chunk_id,
        "text": chunk_text,
        "metadata": {
            "doc_id": doc_id,
            "file_name": file_name,
            "file_type": file_type,
            "source_path": source_path,
            "page": page,
            "section": section,
            "title": title,
            "department": department,
            "chunk_index": chunk_index,
            "chunk_type": "text",
        },
        "chunk_type": "text",
    }


def make_doc_id(file_name: str) -> str:
    """파일명에서 문서 고유 ID를 생성합니다.

    공백, 특수문자를 언더스코어로 대체하고 소문자로 변환합니다.

    Args:
        file_name: 원본 파일명 (확장자 포함)

    Returns:
        정규화된 문서 ID 문자열
    """
    stem = Path(file_name).stem
    # 공백 및 특수문자를 언더스코어로 대체
    doc_id = re.sub(r"[^a-zA-Z0-9가-힣_]", "_", stem)
    return doc_id.lower()


def chunk_extract_result(
    extract_result: dict,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[dict]:
    """extractor.py의 추출 결과를 청크 리스트로 변환합니다.

    각 페이지의 텍스트를 Fixed-size 청킹으로 분할합니다.
    모든 청크에 메타데이터를 부착하여 출처 추적이 가능한 형식으로 반환합니다.

    Args:
        extract_result: extractor.extract_text() 반환값
        chunk_size: 텍스트 청크 최대 문자 수 (기본: 500)
        overlap: 청크 간 오버랩 문자 수 (기본: 100)

    Returns:
        텍스트 청크 딕셔너리와 이미지 캡션 청크 딕셔너리 혼합 리스트
    """
    # === INPUT ===
    file_name = extract_result["file_name"]
    file_type = extract_result["file_type"]
    source_path = extract_result["source_path"]
    pages = extract_result["pages"]

    doc_id = make_doc_id(file_name)
    all_chunks = []
    chunk_counter = 0

    # === PROCESS ===
    for page_data in pages:
        page_num = page_data["page"]
        page_text = page_data.get("text", "")
        title = page_data.get("title", "")
        department = page_data.get("department", "")
        section = page_data.get("section", "")
        caption = page_data.get("caption", "")
        image_path = page_data.get("image_path")
        has_image = page_data.get("has_image", False)

        # 텍스트 청크 생성
        if page_text:
            text_chunks = split_text_into_chunks(page_text, chunk_size, overlap)
            for chunk_text in text_chunks:
                chunk = build_text_chunk(
                    chunk_text=chunk_text,
                    doc_id=doc_id,
                    file_name=file_name,
                    file_type=file_type,
                    source_path=source_path,
                    page=page_num,
                    section=section,
                    title=title,
                    department=department,
                    chunk_index=chunk_counter,
                )
                all_chunks.append(chunk)
                chunk_counter += 1

        # 이미지 캡션 청크 생성 (이미지 캡션이 있는 경우)
        if has_image and caption and image_path:
            img_chunk = build_image_caption_chunk(
                caption=caption,
                image_path=str(image_path),
                doc_id=doc_id,
                file_name=file_name,
                source_path=source_path,
                page=page_num,
                title=title,
                department=department,
                chunk_index=chunk_counter,
            )
            all_chunks.append(img_chunk)
            chunk_counter += 1

    # === OUTPUT ===
    return all_chunks


def chunk_all_documents(
    extract_results: list[dict],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[dict]:
    """여러 문서의 추출 결과를 일괄 청킹하여 전체 청크 리스트를 반환합니다.

    extractor.extract_all_from_directory()의 결과를 입력받아
    각 문서에 대해 chunk_extract_result()를 적용합니다.

    Args:
        extract_results: 여러 문서의 추출 결과 딕셔너리 리스트
        chunk_size: 텍스트 청크 최대 문자 수 (기본: 500)
        overlap: 청크 간 오버랩 문자 수 (기본: 100)

    Returns:
        모든 문서의 청크 딕셔너리 합산 리스트
    """
    if not extract_results:
        print("청킹할 문서가 없습니다.")
        sys.exit(1)

    # === PROCESS ===
    all_chunks = []
    for result in extract_results:
        file_name = result.get("file_name", "알 수 없음")
        chunks = chunk_extract_result(result, chunk_size, overlap)
        text_count = sum(1 for c in chunks if c["chunk_type"] == "text")
        print(f"    {file_name} → {text_count}개 청크")
        all_chunks.extend(chunks)

    # === OUTPUT ===
    print(f"    총 {len(all_chunks)}개 청크 생성")
    return all_chunks
