"""
ko-sroberta-multitask 임베딩 모델로 텍스트를 벡터화하고
ChromaDB에 청크를 저장하는 모듈.

임베딩 모델:
  - 모델명: jhgan/ko-sroberta-multitask
  - 특징: 한국어 특화, SRoBERTa 기반, 문장 유사도 태스크 파인튜닝
  - 최초 실행 시 HuggingFace에서 자동 다운로드 (약 400MB)

ChromaDB:
  - 로컬 영속 모드 (PersistentClient)
  - 컬렉션명: "metacoding_documents"
  - 유사도 측정: cosine 거리 (기본)
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


# =====================================================================
# === INPUT ===
# chunks: chunker.py의 chunk_all_documents() 반환값
# chroma_dir: ChromaDB 저장 디렉토리 경로
# collection_name: ChromaDB 컬렉션명
# embedding_model_name: HuggingFace 임베딩 모델명
# =====================================================================


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


def store_chunks_to_chroma(
    chunks: list[dict],
    chroma_dir: str = DEFAULT_CHROMA_DIR,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    embedding_model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> dict:
    """청크를 임베딩하여 ChromaDB에 저장하는 메인 함수.

    1. 임베딩 모델 로드
    2. ChromaDB 클라이언트 및 컬렉션 초기화
    3. 청크 임베딩 계산
    4. ChromaDB에 배치 단위로 업서트(upsert)

    이미 존재하는 ID의 청크는 덮어쓰기(upsert)되므로
    중복 실행 시 데이터가 중복 저장되지 않습니다.

    Args:
        chunks: chunker.py의 청크 딕셔너리 리스트
        chroma_dir: ChromaDB 영속 저장 디렉토리 경로
        collection_name: ChromaDB 컬렉션명
        embedding_model_name: 사용할 임베딩 모델 HuggingFace ID

    Returns:
        {
            "collection_name": 컬렉션명 (str),
            "chroma_dir": 저장 경로 (str),
            "total_chunks": 처리한 청크 수 (int),
            "collection_count": 저장 후 컬렉션 총 문서 수 (int)
        }

    Raises:
        ValueError: chunks가 비어 있는 경우
        RuntimeError: ChromaDB 저장 중 오류가 발생한 경우
    """
    if not chunks:
        raise ValueError("저장할 청크가 없습니다.")

    chroma_dir = str(Path(chroma_dir).resolve())

    # === PROCESS: Step 1 — 임베딩 모델 로드 ===
    model = load_embedding_model(embedding_model_name)

    # === PROCESS: Step 2 — ChromaDB 초기화 ===
    try:
        client = chromadb.PersistentClient(
            path=chroma_dir,
            settings=Settings(anonymized_telemetry=False),
        )
    except Exception as e:
        raise RuntimeError(
            f"ChromaDB를 초기화할 수 없습니다: {chroma_dir}\n"
            f"디렉토리 권한을 확인하십시오.\n원인: {e}"
        ) from e

    collection = get_or_create_collection(client, collection_name)

    # === PROCESS: Step 3 — 임베딩 계산 ===
    ids, documents, embeddings, metadatas = embed_chunks(chunks, model)

    # === PROCESS: Step 4 — ChromaDB에 배치 업서트 ===
    try:
        for batch_start in range(0, len(ids), BATCH_SIZE):
            batch_end = batch_start + BATCH_SIZE
            collection.upsert(
                ids=ids[batch_start:batch_end],
                documents=documents[batch_start:batch_end],
                embeddings=embeddings[batch_start:batch_end],
                metadatas=metadatas[batch_start:batch_end],
            )
    except Exception as e:
        raise RuntimeError(
            f"ChromaDB 저장 중 오류가 발생했습니다.\n원인: {e}"
        ) from e

    final_count = collection.count()

    # === OUTPUT ===
    return {
        "collection_name": collection_name,
        "chroma_dir": chroma_dir,
        "total_chunks": len(chunks),
        "collection_count": final_count,
    }


def search_chroma(
    query: str,
    chroma_dir: str = DEFAULT_CHROMA_DIR,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    embedding_model_name: str = DEFAULT_EMBEDDING_MODEL,
    top_k: int = 5,
) -> list[dict]:
    """ChromaDB에서 쿼리와 유사한 청크를 검색합니다.

    쿼리 텍스트를 임베딩하여 코사인 유사도 기반으로 상위 k개의
    관련 청크를 반환합니다.

    Args:
        query: 검색 쿼리 텍스트
        chroma_dir: ChromaDB 저장 디렉토리 경로
        collection_name: 검색할 ChromaDB 컬렉션명
        embedding_model_name: 임베딩 모델 HuggingFace ID
        top_k: 반환할 최대 검색 결과 수 (기본: 5)

    Returns:
        [
            {
                "rank": 순위 (int),
                "text": 청크 텍스트 (str),
                "distance": 코사인 거리 (float, 낮을수록 유사),
                "metadata": 청크 메타데이터 딕셔너리
            }, ...
        ]

    Raises:
        RuntimeError: ChromaDB 로드 또는 검색 중 오류 발생 시
    """
    chroma_dir_path = Path(chroma_dir)
    if not chroma_dir_path.exists():
        print(f"ChromaDB 디렉토리가 없습니다: {chroma_dir}")
        print("main.py를 먼저 실행하여 문서를 색인하십시오.")
        sys.exit(1)

    # === PROCESS ===
    model = load_embedding_model(embedding_model_name)
    query_embedding = model.encode(
        [query], normalize_embeddings=True
    ).tolist()

    try:
        client = chromadb.PersistentClient(
            path=str(chroma_dir_path.resolve()),
            settings=Settings(anonymized_telemetry=False),
        )
        collection = client.get_collection(name=collection_name)
    except Exception as e:
        raise RuntimeError(
            f"ChromaDB를 로드할 수 없습니다: {chroma_dir}\n"
            f"main.py를 먼저 실행하여 색인을 생성하십시오.\n원인: {e}"
        ) from e

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "distances", "metadatas"],
    )

    # === OUTPUT ===
    search_results = []
    docs = results.get("documents", [[]])[0]
    dists = results.get("distances", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    for rank, (doc, dist, meta) in enumerate(zip(docs, dists, metas), start=1):
        search_results.append(
            {
                "rank": rank,
                "text": doc,
                "distance": round(dist, 4),
                "metadata": meta,
            }
        )

    return search_results
