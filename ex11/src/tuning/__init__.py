"""ex11 튜닝 도메인 계층.

챕터 8·9에서 만든 튜닝 부품을 각각 독립된 객체로 분리해 둔 곳이다.
`pipeline.py`의 `RagPipeline`이 이 객체들을 주입받아 조립해 사용한다.

- QueryExpander              (CH09) — 약어·동의어 확장
- BM25Retriever              (CH08) — rank-bm25 키워드 검색
- EnsembleRetriever          (CH08) — BM25 + ChromaDB(Vector) 하이브리드 검색
- CrossEncoderReranker       (CH08) — 딥러닝 리랭커
- SimpleReranker             (CH08) — 리랭커 폴백(키워드 오버랩)
- ParentDocumentRetriever    (CH09) — 자식 검색 결과를 부모 원문으로 복원

인덱싱 단계의 하이브리드 파서(CH10)는 `hybrid_parser` 모듈에 있다.
"""

from .bm25_retriever import BM25Retriever
from .ensemble_retriever import EnsembleRetriever
from .hybrid_parser import parse_pdf_hybrid
from .parent_doc import ParentDocumentRetriever
from .query_expander import DEFAULT_ABBREVIATIONS, QueryExpander
from .reranker import CrossEncoderReranker, SimpleReranker

__all__ = [
    "BM25Retriever",
    "CrossEncoderReranker",
    "DEFAULT_ABBREVIATIONS",
    "EnsembleRetriever",
    "ParentDocumentRetriever",
    "QueryExpander",
    "SimpleReranker",
    "parse_pdf_hybrid",
]
