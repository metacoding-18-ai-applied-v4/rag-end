"""step3 — 파이프라인 부품 모음 (완성 코드).

평가 프레임워크에 끼워 넣을 수 있는 부품을 함수로 제공한다.
CH08~09 튜닝 기법을 평가용 경량 버전으로 ex10 안에 복제했다.
각 함수는 다섯 영역 중 하나에 속한다.

- parse: Path → list[str]      (페이지별 텍스트)
- chunk: (pages, source) → list[dict]
- query_transform: str → str
- retrieve: (collection, query, k) → list[dict]
- rerank: (query, docs) → list[dict]
"""

from __future__ import annotations

import fitz  # PyMuPDF


# ---------------------------------------------------------------------------
# 1. Parsing — pypdf text vs Hybrid(+Vision)
# ---------------------------------------------------------------------------

def parse_pypdf(pdf_path) -> list[str]:
    """PDF 텍스트 레이어만 추출한다. 스캔본은 빈 문자열."""
    doc = fitz.open(str(pdf_path))
    pages = [doc[i].get_text() for i in range(len(doc))]
    doc.close()
    return pages


def parse_hybrid(pdf_path) -> list[str]:
    """pypdf 텍스트가 부족하면 Vision LLM으로 전환.

    step2_hybrid_parser.process_page_hybrid를 재사용한다.
    """
    from ..step2_hybrid_parser.hybrid_parser import process_page_hybrid

    doc = fitz.open(str(pdf_path))
    pages = []
    for page in doc:
        result = process_page_hybrid(page)
        pages.append(result.get("text", ""))
    doc.close()
    return pages


# ---------------------------------------------------------------------------
# 2. Chunking — Page vs Semantic(paragraph-level)
# ---------------------------------------------------------------------------

def chunk_page(pages: list[str], source: str) -> list[dict]:
    """페이지 단위 청킹. 한 페이지 = 한 청크."""
    chunks = []
    for page_num, text in enumerate(pages, 1):
        if text.strip():
            chunks.append({
                "id": f"{source}_p{page_num}",
                "text": text[:5000],
                "source": source,
                "page": page_num,
            })
    return chunks


def chunk_semantic(pages: list[str], source: str) -> list[dict]:
    """단락 단위 청킹(CH08 semantic chunking의 경량 버전).

    빈 줄(`\\n\\n`)을 경계로 분리한 뒤 너무 짧은 조각은 흡수한다.
    페이지 청킹보다 더 세밀한 검색 단위를 제공한다.
    """
    chunks = []
    MIN_CHUNK_LEN = 40
    for page_num, text in enumerate(pages, 1):
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        # 짧은 조각은 다음 조각과 합친다
        merged: list[str] = []
        buffer = ""
        for para in paragraphs:
            combined = f"{buffer}\n{para}".strip() if buffer else para
            if len(combined) < MIN_CHUNK_LEN:
                buffer = combined
                continue
            merged.append(combined)
            buffer = ""
        if buffer:
            if merged:
                merged[-1] = f"{merged[-1]}\n{buffer}".strip()
            else:
                merged.append(buffer)

        for j, para in enumerate(merged, 1):
            chunks.append({
                "id": f"{source}_p{page_num}_c{j}",
                "text": para[:5000],
                "source": source,
                "page": page_num,
            })
    return chunks


# ---------------------------------------------------------------------------
# 3. Query transform — No-op vs Abbreviation expansion
# ---------------------------------------------------------------------------

# 사내 약어 사전(CH09 abbreviation expansion의 경량 버전)
ABBREVIATIONS = {
    "WFH": "재택근무",
    "OT": "초과근무",
    "연차": "연차 휴가",
    "병가": "병가 유급휴가",
    "DLP": "데이터 유출 방지",
    "VPN": "가상사설망",
    "USB": "USB 외부저장장치",
}


def query_noop(query: str) -> str:
    """원본 질문 그대로."""
    return query


def query_expand_abbreviations(query: str) -> str:
    """사내 약어를 풀어 붙여 검색 재현율을 높인다(CH09 경량 버전)."""
    expanded = query
    for abbr, full in ABBREVIATIONS.items():
        if abbr in expanded and full not in expanded:
            expanded = expanded.replace(abbr, f"{abbr}({full})")
    return expanded


# ---------------------------------------------------------------------------
# 4. Retrieval — Cosine vs Parent-doc
# ---------------------------------------------------------------------------

def retrieve_cosine(collection, query: str, k: int) -> list[dict]:
    """ChromaDB cosine 검색."""
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
    return retrieved


def retrieve_parent_doc(collection, query: str, k: int) -> list[dict]:
    """자식 청크 검색 후 같은 (source, page)의 형제 청크를 합쳐 부모 문맥을 돌려준다.

    CH09 ParentDocumentRetriever의 경량 버전. 세밀한 청크로 검색하되
    답변 생성에는 더 넓은 문맥을 제공한다.
    """
    # 자식 청크 3배수로 넉넉히 뽑아 부모로 접는다
    children = retrieve_cosine(collection, query, k * 3)

    parents: dict[tuple, dict] = {}
    for ch in children:
        parent_key = (ch["source"], ch["page"])
        if parent_key not in parents:
            parents[parent_key] = {
                "id": f"{ch['source']}_p{ch['page']}",
                "text": ch["text"],
                "source": ch["source"],
                "page": ch["page"],
                "distance": ch["distance"],
                "_child_count": 1,
            }
        else:
            parent = parents[parent_key]
            parent["text"] = f"{parent['text']}\n{ch['text']}"
            parent["_child_count"] += 1
            parent["distance"] = min(parent["distance"], ch["distance"])

    ordered = sorted(parents.values(), key=lambda r: r["distance"])
    for r in ordered:
        r.pop("_child_count", None)
    return ordered[:k]


# ---------------------------------------------------------------------------
# 5. Rerank — No-op vs Keyword-overlap
# ---------------------------------------------------------------------------

def rerank_noop(query: str, docs: list[dict]) -> list[dict]:
    """재정렬 없음."""
    return docs


def rerank_keyword(query: str, docs: list[dict]) -> list[dict]:
    """쿼리·문서 토큰 오버랩 기반 재정렬(CH08 CrossEncoderReranker의 경량 버전).

    실제 CrossEncoder 모델 대신 단순 단어 교집합 개수를 점수로 쓴다.
    벡터 유사도 순위에 어휘 일치를 덧씌워 보정한다.
    """
    q_tokens = {w for w in query.lower().split() if len(w) > 1}
    scored = []
    for d in docs:
        text_tokens = {w for w in d["text"].lower().split() if len(w) > 1}
        overlap = len(q_tokens & text_tokens)
        scored.append((overlap, d.get("distance", 0.0), d))
    # overlap 높을수록, distance 낮을수록 앞쪽
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [d for _, _, d in scored]
