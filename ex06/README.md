# ex06 — 정형 MCP + 비정형 RAG 통합 에이전트 설계

> 사내 AI 비서 ex06: QueryRouter + ReAct Agent + MCP Tools + 채팅 UI

## 개요

이 예제는 정형 데이터(PostgreSQL DB)와 비정형 데이터(사내 문서)를 통합하여
복합적인 HR 질문에 답변하는 에이전트를 구현합니다.

**3단계 라우팅 전략:**
1. Step 1 — 규칙 기반: 키워드 매칭으로 빠르게 분류
2. Step 2 — 스키마 기반: DB 컬럼명 감지로 정형 질문 식별
3. Step 3 — LLM 판단: 모호한 질문을 LLM이 최종 분류

**10개 대표 시나리오:**
- 정형(4): 연차 잔여, 매출 합계, 직원 목록, 부서별 통계
- 비정형(4): 온보딩 절차, 보안 정책, 복지 안내, 출장 규정
- 복합(2): 매출 상위 부서의 복지 정책, 특정 직원의 연차 규정

정형 데이터 도구는 **PostgreSQL 연결이 필수**입니다. `docker compose up -d`로 DB를 시작한 후 실행하십시오.

---

## 빠른 시작

```bash
cd ex06
python3.12 -m venv .venv
source .venv/bin/activate
cp .env.example .env
pip install -r requirements.txt

# 1. PostgreSQL 시작 (필수)
docker compose up -d

# 2. 단위 테스트 실행
python -m pytest tests/test_scenarios.py -v
```

---

## 전체 실행 (FastAPI 웹 UI)

### 1단계: 환경 변수 설정

```bash
cp .env.example .env
# .env 파일에서 LLM_PROVIDER 및 관련 키를 설정하세요
```

### 2단계: PostgreSQL 시작 (필수)

```bash
docker compose up -d
```

### 3단계: LLM 준비

ex06은 Tool Calling이 필요하므로 `llama3.1:8b`를 사용합니다.

```bash
ollama pull llama3.1:8b
```

OpenAI 사용 시 `.env`에서 `LLM_PROVIDER=openai`로 변경하고
`OPENAI_API_KEY`를 설정합니다.

### 4단계: 서버 실행

```bash
uvicorn app.main:app --reload --port 8008
```

브라우저에서 `http://localhost:8008/chat` 접속

---

## 프로젝트 구조

```
ex06/
├── README.md               # 이 파일
├── requirements.txt        # Python 의존성 (버전 고정)
├── .env.example            # 환경 변수 템플릿
├── docker-compose.yml      # PostgreSQL 16 컨테이너
├── src/
│   ├── __init__.py
│   ├── router.py           # QueryRouter (3단계 라우팅)
│   ├── mcp_tools.py        # MCP 도구 4개 (DB 연결 필수)
│   └── agent.py            # ReAct 통합 에이전트
├── app/
│   ├── __init__.py
│   ├── database.py         # PostgreSQL 연결 (필수)
│   ├── chat_api.py         # FastAPI 라우터 + 채팅 엔드포인트
│   └── main.py             # FastAPI 앱 진입점
├── templates/
│   ├── base.html           # 사이드바 레이아웃 (Inter 폰트, 골드 강조)
│   └── chat.html           # 채팅 UI (에이전트 모드 토글 + 질문 유형 배지)
├── static/
│   ├── css/
│   │   ├── style.css       # 기본 레이아웃
│   │   └── chat.css        # 채팅 버블 + 배지 + 아코디언
│   └── js/
│       └── chat.js         # 채팅 로직 + 로컬스토리지
├── tests/
│   └── test_scenarios.py   # 18개 단위 테스트
├── data/
│   ├── schema.sql          # PostgreSQL 스키마 + 샘플 데이터
│   └── chroma_db/          # ChromaDB 저장소 (선택)
└── outputs/                # 실행 결과 저장 (.gitignore 대상)
```

---

## 핵심 코드 설명

### QueryRouter (src/router.py)

**다음 코드는 사용자 질문을 3단계 전략으로 분류하여 처리 경로를 결정합니다.**

```python
step1_result = self._step1_rule_based(query)   # ①
step2_result = self._step2_schema_based(query)  # ②
step3_result = self._step3_llm_based(query)     # ③
return step3_result or "unstructured"           # ④
```

> ① 키워드 매칭: 연차/매출/목록 → structured, 절차/정책/안내 → unstructured
> ② 스키마 매칭: remaining_days, total_amount 등 DB 컬럼명 감지
> ③ LLM 판단: Step 1,2에서 미결정 시 LLM이 JSON으로 분류
> ④ 기본값: 모두 실패하면 비정형으로 처리

### MCP 도구 (src/mcp_tools.py)

**다음 코드는 PostgreSQL에서 연차 잔여일수를 조회합니다. DB 연결은 필수입니다.**

```python
rows = _run_query("SELECT ... FROM employees WHERE emp_no = %s", (emp_no,))  # ①
if rows:
    return rows[0]                    # ②
return {"error": f"직원 '{emp_no}'을(를) 찾을 수 없습니다."}  # ③
```

> ① PostgreSQL 조회 시도 (connect_timeout=3으로 빠른 실패)
> ② DB 결과가 있으면 즉시 반환
> ③ DB 미연결 또는 미발견 시 에러 메시지 반환

### ReAct 에이전트 (src/agent.py)

**다음 코드는 Tool Calling 에이전트가 MCP 도구를 반복 실행하며 복합 질문을 해결합니다.**

```python
query_type = self._router.classify_query(query)          # ①
result = self._agent_executor.invoke({"input": query})   # ②
answer = re.sub(r"<think>.*?</think>", "", answer)       # ③
structured_data, unstructured_data = self._parse_result(steps)  # ④
```

> ① QueryRouter로 질문 유형 먼저 분류
> ② AgentExecutor가 도구를 선택·실행하며 최종 답변 생성
> ③ DeepSeek-R1 등의 `<think>` 태그를 최종 답변에서 제거
> ④ 중간 단계(intermediate_steps)에서 DB/문서 데이터를 추출

---

## API 명세

### POST /api/chat

**요청:**

```json
{
  "query": "김민준 연차 잔여일수 알려줘",
  "use_agent": true
}
```

**응답:**

```json
{
  "query": "김민준 연차 잔여일수 알려줘",
  "answer": "김민준 과장님의 연차 잔여일수는 8일입니다.",
  "query_type": "structured",
  "mode": "agent",
  "structured_data": {
    "leave_balance": {
      "name": "김민준",
      "remaining_days": 8,
      "used_days": 7,
      "total_days": 15
    }
  },
  "unstructured_data": [],
  "steps": [
    {"tool": "leave_balance", "input": {"emp_no": "김민준"}, "output": "..."}
  ]
}
```

---

## 외부 서비스 의존성

| 서비스 | 필수 여부 | 미연결 시 동작 |
|--------|:--------:|-------------|
| PostgreSQL | **필수** | 정형 데이터 도구가 에러 반환 |
| ChromaDB | 선택 | `data/docs/` 키워드 검색으로 대체 |
| LLM (Ollama/OpenAI) | 선택 | QueryRouter Step 1, 2만으로 라우팅 결정 |

---

## 환경 요구사항

- Python 3.12 이상
- Docker Desktop: PostgreSQL 컨테이너 실행 (**필수**)
- Ollama 또는 OpenAI API 키: LLM 실행
