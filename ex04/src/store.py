"""벡터DB 저장+검색 — ChromaDB에 청크를 넣고 검색하는 핵심 로직.

CH04 핵심: 임베딩 → upsert 저장, 쿼리 → 유사도 검색
"""

from _store_utils import (
    load_embedding_model,
    get_or_create_collection,
    embed_chunks,
    DEFAULT_CHROMA_DIR,
    DEFAULT_COLLECTION_NAME,
    DEFAULT_EMBEDDING_MODEL,
    BATCH_SIZE,
)
import sys
from pathlib import Path
import chromadb
from chromadb.config import Settings


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

    # TODO: 위 4단계를 순서대로 구현합니다
    model = load_embedding_model(embedding_model_name)

    client = chromadb.PersistentClient(
        path=chroma_dir,
        settings=Settings(anonymized_telemetry=False),
    )
    collection = get_or_create_collection(client, collection_name)

    ids, documents, embeddings, metadatas = embed_chunks(chunks, model)

    for batch_start in range(0, len(ids), BATCH_SIZE):
        batch_end = batch_start + BATCH_SIZE
        collection.upsert(
            ids=ids[batch_start:batch_end],
            documents=documents[batch_start:batch_end],
            embeddings=embeddings[batch_start:batch_end],
            metadatas=metadatas[batch_start:batch_end],
        )

    return {
        "collection_name": collection_name,
        "chroma_dir": chroma_dir,
        "total_chunks": len(chunks),
        "collection_count": collection.count(),
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

    # TODO: 쿼리 임베딩 → collection.query() → 결과 정리
    model = load_embedding_model(embedding_model_name)
    query_embedding = model.encode([query], normalize_embeddings=True).tolist()

    client = chromadb.PersistentClient(
        path=str(chroma_dir_path.resolve()),
        settings=Settings(anonymized_telemetry=False),
    )
    collection = client.get_collection(name=collection_name)

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "distances", "metadatas"],
    )

    search_results = []
    docs = results.get("documents", [[]])[0]
    dists = results.get("distances", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    for rank, (doc, dist, meta) in enumerate(zip(docs, dists, metas), start=1):
        search_results.append({
            "rank": rank, "text": doc,
            "distance": round(dist, 4), "metadata": meta,
        })

    return search_results
