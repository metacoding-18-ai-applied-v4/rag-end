"""ex08 RAG 튜닝 - 튜닝 실험 패키지.

step 구조:
  step1_chunk_experiment/  - 청킹 전략 + Retriever 파라미터 실험 (패키지)
  step2_reranker/          - Cross-Encoder 리랭킹 (패키지)
  step3_hybrid_search.py   - BM25+Vector 앙상블 검색 (단일 파일)

레거시 모듈 (개별 실험용):
  chunk_experiment     - Fixed-size vs Semantic 청킹 비교
  retriever_experiment - k값, threshold, metadata filter 실험
  reranker             - Cross-Encoder 기반 재정렬
  hybrid_search        - BM25 + Vector 앙상블 검색
  advanced_retriever   - ParentDocument, SelfQuery, Compression
  query_rewrite        - HyDE, Multi-Query, 약어 확장
  document_parser      - 라이브러리 vs vLLM 파싱 전략 비교
  document_capture     - 문서 캡처 + 인제스천 파이프라인
  evidence_pipeline    - 답변 근거 시스템
"""
