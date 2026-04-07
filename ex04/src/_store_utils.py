"""
벡터DB 유틸리티 — 임베딩 모델 로드, 컬렉션 관리, 청크 임베딩 등
store.py에서 import하여 사용합니다.
"""

import sys
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# 기본 설정 상수
DEFAULT_CHROMA_DIR = "./data/chroma_db"
DEFAULT_COLLECTION_NAME = "metacoding_documents"
DEFAULT_EMBEDDING_MODEL = "jhgan/ko-sroberta-multitask"
BATCH_SIZE = 64  # 임베딩 배치 크기 (메모리 제약 환경에서 조정)


def load_embedding_model(model_name: str = DEFAULT_EMBEDDING_MODEL) -> SentenceTransformer:
    """ko-sroberta-multitask 임베딩 모델을 로드합니다.

    최초 실행 시 HuggingFace에서 모델을 다운로드하고
    로컬 캐시(~/.cache/huggingface/)에 저장합니다.
    이후 실행에서는 캐시를 재사용합니다.

    Args:
        model_name: HuggingFace 모델 ID
                   (기본값: "jhgan/ko-sroberta-multitask")

    Returns:
        로드된 SentenceTransformer 모델 인스턴스

    Raises:
        RuntimeError: 모델 다운로드 또는 로드에 실패한 경우
    """
    try:
        model = SentenceTransformer(model_name)
        return model
    except Exception as e:
        raise RuntimeError(
            f"임베딩 모델을 로드할 수 없습니다: {model_name}\n"
            f"인터넷 연결을 확인하거나 모델명을 다시 확인하십시오.\n원인: {e}"
        ) from e


def get_or_create_collection(
    client: chromadb.PersistentClient,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> chromadb.Collection:
    """ChromaDB 컬렉션을 가져오거나 없으면 새로 생성합니다.

    컬렉션이 이미 존재하는 경우 기존 컬렉션을 반환합니다.
    cosine 유사도를 사용하도록 메타데이터를 설정합니다.

    Args:
        client: ChromaDB PersistentClient 인스턴스
        collection_name: 컬렉션명 (기본값: "metacoding_documents")

    Returns:
        ChromaDB Collection 인스턴스
    """
    # === PROCESS ===
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},  # cosine 유사도 사용
    )
    # === OUTPUT ===
    return collection


def embed_chunks(
    chunks: list[dict],
    model: SentenceTransformer,
) -> tuple[list[str], list[str], list[list[float]], list[dict]]:
    """청크 리스트에서 ChromaDB 저장에 필요한 4가지 구성 요소를 추출합니다.

    배치 단위로 임베딩을 계산하여 메모리 효율을 높입니다.

    Args:
        chunks: chunker.py의 청크 딕셔너리 리스트
        model: 로드된 SentenceTransformer 임베딩 모델

    Returns:
        (ids, documents, embeddings, metadatas) 튜플:
        - ids: 청크 고유 ID 리스트
        - documents: 청크 텍스트 리스트
        - embeddings: 임베딩 벡터 리스트 (float 리스트의 리스트)
        - metadatas: 청크 메타데이터 딕셔너리 리스트

    Raises:
        ValueError: chunks가 비어 있는 경우
    """
    if not chunks:
        raise ValueError("임베딩할 청크가 없습니다. 문서 파싱이 정상적으로 완료되었는지 확인하십시오.")

    # === PROCESS ===
    ids = [c["id"] for c in chunks]
    documents = [c["text"] for c in chunks]

    # 메타데이터에서 ChromaDB 허용 타입이 아닌 값 변환 (None → "")
    metadatas = []
    for c in chunks:
        meta = {}
        for k, v in c["metadata"].items():
            if v is None:
                meta[k] = ""
            elif isinstance(v, bool):
                meta[k] = str(v)
            else:
                meta[k] = v
        metadatas.append(meta)

    # 배치 단위 임베딩 계산
    all_embeddings = []
    for batch_start in range(0, len(documents), BATCH_SIZE):
        batch_texts = documents[batch_start : batch_start + BATCH_SIZE]
        batch_embeddings = model.encode(
            batch_texts, show_progress_bar=False, normalize_embeddings=True
        )
        all_embeddings.extend(batch_embeddings.tolist())

    # === OUTPUT ===
    return ids, documents, all_embeddings, metadatas
