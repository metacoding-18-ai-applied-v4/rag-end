# ex01 LLM의 한계와 RAG의 필요성

> 사내 AI 비서 (RAG + MCP) - ex01 실습 코드

## 학습 목표

- LLM의 환각(Hallucination) 현상을 직접 체험하고 원인을 이해합니다.
- Context Injection의 작동 원리와 한계를 체감합니다.
- RAG(Retrieval-Augmented Generation)가 환각 문제를 어떻게 해결하는지 확인합니다.
- DeepSeek R1의 Chain-of-Thought 추론 능력을 RAG와 결합하여 활용합니다.

## 폴더 구조

```
ex01/
├── step1_fail.py              # [실패] LLM 단독 질의 → 환각 체험
├── step2_context.py           # [임시 해결] Context Injection
├── step3_rag.py               # [성공] RAG + 청킹 적용
├── step3_rag_no_chunking.py   # [비교] RAG 청킹 미적용
├── step4_rag.py               # [심화] RAG + 추론(Reasoning)
├── requirements.txt           # 의존성 목록
└── docs/                      # 튜토리얼 가이드 문서
```

## 4단계 실습 구성

| 스크립트 | 단계 | 핵심 체험 |
|---------|------|---------|
| `step1_fail.py` | 실패 | LLM 단독 질의 → 환각 응답 체험 |
| `step2_context.py` | 임시 해결 | 프롬프트에 문서 직접 삽입 → 정확도 향상 |
| `step3_rag.py` | 성공 | 청킹 적용 RAG — 관련 문서만 검색하여 답변 |
| `step3_rag_no_chunking.py` | 비교 | 청킹 미적용 RAG — 통째로 검색하여 비효율 체감 |
| `step4_rag.py` | 심화 | RAG + 추론 — 규정 기반 계산 질문 |

## 실행 환경

- Python 3.12
- Ollama + DeepSeek R1:8b 모델
- Ollama + nomic-embed-text 임베딩 모델

## 사전 준비

### Ollama 모델 다운로드

```bash
ollama pull deepseek-r1:8b
ollama pull nomic-embed-text
```

### Ollama 서버 실행

```bash
ollama serve
```

## 설치 및 실행

```bash
cd code/ex01
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 의존성 설명

| 패키지 | 역할 |
|-------|------|
| `langchain` | LLM 애플리케이션 프레임워크 (체인, 프롬프트 관리) |
| `langchain-ollama` | Ollama LLM/임베딩 연결 (`ChatOllama`, `OllamaEmbeddings`) |
| `langchain-chroma` | ChromaDB 벡터스토어 연결 |
| `langchain-classic` | `RetrievalQA` 등 레거시 체인 지원 |
| `chromadb` | 인메모리 벡터 데이터베이스 |

## 실행 순서

4개의 스크립트를 순서대로 실행합니다.

```bash
# 1단계: LLM 단독 질의 (환각 체험)
python step1_fail.py

# 2단계: Context Injection
python step2_context.py

# 3단계: RAG 미리보기 (청킹 적용 vs 미적용 비교)
python step3_rag_no_chunking.py
python step3_rag.py

# 4단계: RAG + 추론
python step4_rag.py
```

## 자주 발생하는 오류

| 오류 메시지 | 원인 | 해결 방법 |
|------------|------|---------|
| `Connection refused` | Ollama가 실행되지 않음 | `ollama serve` 실행 |
| `model not found` | 모델 미다운로드 | `ollama pull deepseek-r1:8b` |
| `nomic-embed-text` 관련 오류 | 임베딩 모델 미다운로드 | `ollama pull nomic-embed-text` |
| 응답이 너무 느림 | RAM 부족 | `deepseek-r1:1.5b` 소형 모델로 전환 |

## 다음 버전

- **v0.2**: FastAPI + PostgreSQL로 사내 시스템(직원/휴가/매출 CRUD)을 구축합니다.
- **v0.3**: 인메모리 ChromaDB를 디스크에 영속화하고 실제 PDF 문서를 인덱싱합니다.
