"""ex07 LangChain Agent 구성."""

import logging
import os
import time

from dotenv import load_dotenv

from .cache import response_cache
from .monitoring import token_tracker
from ._rich_logging import console
from .tools import get_leave_balance, get_sales_sum, list_employees, search_documents
from .router import QueryRouter
from .llm_factory import build_llm
from ._agent_utils import build_agent_executor, run_with_retry

load_dotenv()

logger = logging.getLogger(__name__)

# --- 시스템 프롬프트 ---
SYSTEM_PROMPT = """당신은 사내 AI 비서입니다.
사내 인사(HR) 시스템과 문서를 연결하여 직원들의 업무 질문에 정확하게 답변합니다.

[보유 도구]
- list_employees: 직원 목록 조회 (부서 필터 가능)
- get_leave_balance: 특정 직원의 휴가 잔여 일수 조회
- get_sales_sum: 부서별 또는 전체 매출 합계 조회
- search_documents: 사내 규정·가이드·정책 문서 검색

[도구 사용 원칙]
1. 직원 이름이나 부서가 포함된 질문 → list_employees 또는 get_leave_balance 사용
2. 매출·실적 관련 질문 → get_sales_sum 사용
3. 규정·정책·절차에 관한 질문 → search_documents 사용
4. 복합 질문(예: "홍길동의 휴가와 연차 규정") → 여러 도구를 순서대로 호출
5. 도구가 필요 없는 일상 대화 → 직접 답변

답변은 항상 한국어로 작성하고, 출처가 있을 경우 함께 표시하십시오.
"""


class ConnectHRAgent:
    """사내 AI 비서 에이전트."""

    def __init__(self):
        """ConnectHRAgent를 초기화합니다."""
        logger.info("[ConnectHRAgent] 초기화 시작...")

        self.llm = build_llm()
        self._router = QueryRouter(llm=self.llm)
        self.tools = [list_employees, get_leave_balance, get_sales_sum, search_documents]
        self.agent_executor = build_agent_executor(self.llm, self.tools, SYSTEM_PROMPT)

        logger.info(
            "[ConnectHRAgent] 초기화 완료 (도구 수: %d)",
            len(self.tools),
        )

    def run(self, query, chat_history=None, use_cache=True):
        """사용자 질문을 처리하고 답변을 반환합니다."""
        # TODO: run — 캐시 → 분류 → 에이전트 실행(재시도) → 토큰 기록 → 캐시 저장 (5단계)
        start_time = time.time()
        console.print(f"[bold cyan]질문 수신[/bold cyan] [dim]|[/dim] {query}")
        logger.info("[ConnectHRAgent] 질문 수신: %s", query[:80])

        # 1. 캐시 조회 — 같은 질문이면 LLM·DB를 건너뛰고 즉시 반환
        if use_cache:
            cached = response_cache.get(query)
            if cached is not None:
                cached["from_cache"] = True
                console.print("[bold green]ResponseCache HIT[/bold green] [dim]|[/dim] LLM·DB 호출 없이 즉시 반환")
                logger.info("[ConnectHRAgent] 캐시 응답 반환")
                return cached

        # 2. Router로 질문 유형 분류 — 라벨만 붙이고 실행 경로는 그대로 유지
        query_type = self._router.classify_query(query)

        # 3. Agent 실행 — 단일 경로(ex06의 IntegratedAgent와 동일), run_with_retry가 최대 3회 재시도
        if self.agent_executor is not None:
            result = run_with_retry(self.agent_executor, query, chat_history)
        else:
            result = {
                "output": "죄송합니다. 에이전트 서비스를 사용할 수 없습니다.",
                "intermediate_steps": [],
            }
        result["query_type"] = query_type
        result["from_cache"] = False

        # 4. 토큰 사용량 기록 — 모델·입출력 토큰·지연시간을 TokenTracker에 누적
        latency_ms = (time.time() - start_time) * 1000
        provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        if provider == "openai":
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        else:
            # Tool Calling 지원 모델. .env의 OLLAMA_MODEL로 덮어쓸 수 있다.
            model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        token_tracker.record(
            model=model,
            input_tokens=len(query.split()) * 2,
            output_tokens=len(result["output"].split()) * 2,
            operation="agent_run",
            latency_ms=latency_ms,
        )

        # 5. 캐시 저장 — 다음에 같은 질문이 오면 1단계에서 바로 꺼내 쓰도록
        if use_cache:
            response_cache.set(query, result)

        logger.info(
            "[ConnectHRAgent] 처리 완료 (유형: %s, 소요: %.0fms)",
            query_type,
            latency_ms,
        )
        console.print(
            f"[bold cyan]처리 완료[/bold cyan] [dim]|[/dim] 유형={query_type} · 소요={latency_ms:.0f}ms"
        )
        return result


# --- 싱글톤 인스턴스 ---
_agent_instance = None


def get_agent():
    """ConnectHRAgent 싱글톤 인스턴스를 반환합니다."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ConnectHRAgent()
    return _agent_instance
