"""step3 — 평가 실행 보조 함수 (완성 코드).

벡터DB 구축, 검색, LLM 답변 생성, 테스트 질문 로드 등을 제공한다.
"""

import json
import os
from pathlib import Path

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")


def build_vectordb(collection_name: str = "eval_documents") -> chromadb.Collection:
    """data/docs 폴더의 문서를 파싱하여 ChromaDB 컬렉션에 저장한다."""
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )

    try:
        client.delete_collection(collection_name)
    except (ValueError, Exception):
        pass

    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    docs_dir = DATA_DIR / "docs"
    if not docs_dir.exists():
        return collection

    ids = []
    documents = []
    metadatas = []

    for doc_path in sorted(docs_dir.iterdir()):
        if doc_path.suffix.lower() == ".pdf":
            pages = _extract_pdf_text(doc_path)
            for page_num, text in enumerate(pages, 1):
                if text.strip():
                    doc_id = f"{doc_path.stem}_p{page_num}"
                    ids.append(doc_id)
                    documents.append(text[:5000])
                    metadatas.append({
                        "source": doc_path.stem,
                        "page": str(page_num),
                        "format": "pdf",
                    })

    if ids:
        collection.add(ids=ids, documents=documents, metadatas=metadatas)

    return collection


def _extract_pdf_text(pdf_path: Path) -> list[str]:
    """PDF에서 페이지별 텍스트를 추출한다."""
    try:
        import fitz

        doc = fitz.open(str(pdf_path))
        pages = [doc[i].get_text() for i in range(len(doc))]
        doc.close()
        return pages
    except ImportError:
        return []


def search_collection(
    collection: chromadb.Collection,
    query: str,
    k: int = 5,
) -> dict:
    """컬렉션에서 질문에 대해 상위 K개 결과를 검색한다."""
    results = collection.query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []
    for i in range(len(results["ids"][0])):
        retrieved.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "source": results["metadatas"][0][i].get("source", ""),
            "page": results["metadatas"][0][i].get("page", ""),
            "distance": results["distances"][0][i],
        })

    return {
        "query": query,
        "retrieved": retrieved,
        "sources": [r["source"] for r in retrieved],
    }


def generate_answer(query: str, context_docs: list[str]) -> str:
    """검색된 컨텍스트를 기반으로 LLM 답변을 생성한다."""
    try:
        import httpx

        context = "\n\n---\n\n".join(context_docs[:3])
        prompt = (
            f"다음 문서 내용을 참고하여 질문에 답하세요.\n\n"
            f"[문서]\n{context}\n\n"
            f"[질문]\n{query}\n\n"
            f"[답변]"
        )

        resp = httpx.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        return f"[답변 생성 실패: {str(e)[:80]}]"


def load_test_questions() -> list[dict]:
    """test_questions.json을 로드한다."""
    questions_path = DATA_DIR / "test_questions.json"
    if not questions_path.exists():
        return []

    with open(questions_path, encoding="utf-8") as f:
        data = json.load(f)

    return data.get("questions", [])
