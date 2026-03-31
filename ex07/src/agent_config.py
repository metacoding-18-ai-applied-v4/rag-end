"""ex07 LangChain Agent 구성."""

import logging
import os
import time

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from .cache import response_cache
from .monitoring import langfuse_monitor, token_tracker
from .tools import get_leave_balance, get_sales_sum, list_employees, search_documents
from .router import QueryRouter
from .llm_factory import build_llm
from .agent_helpers import build_rag_chain, classify_route

load_dotenv()

logger = logging.getLogger(__name__)

# --- 설정 상수 ---
AGENT_MAX_ITERATIONS = 10   # Agent 최대 반복 횟수
AGENT_TIMEOUT_SECONDS = 60  # Agent 실행 최대 대기 시간 (초)
RETRY_MAX_ATTEMPTS = 3      # 최대 재시도 횟수
RETRY_DELAY_SECONDS = 2.0   # 재시도 간격 (초)

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
        self.rag_chain = build_rag_chain(self.llm)

        self.agent_executor = self._build_agent_executor()

        logger.info(
            "[ConnectHRAgent] 초기화 완료 (도구 수: %d, RAG 체인: %s)",
            len(self.tools),
            "활성" if self.rag_chain else "비활성",
        )

    def _build_agent_executor(self):
        """AgentExecutor를 구성합니다."""
        try:
            # ① 프롬프트 템플릿 정의
            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])

            # ② Tool Calling Agent 생성
            agent = create_tool_calling_agent(self.llm, self.tools, prompt)

            # ③ AgentExecutor 래핑 (운영 설정 포함)
            executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                max_iterations=AGENT_MAX_ITERATIONS,
                max_execution_time=AGENT_TIMEOUT_SECONDS,
                handle_parsing_errors=True,
                return_intermediate_steps=True,
                verbose=True,
            )

            logger.info("[ConnectHRAgent] AgentExecutor 구성 완료")
            return executor

        except Exception as exc:
            logger.error("[ConnectHRAgent] AgentExecutor 구성 실패: %s", exc)
            return None

    def _run_with_retry(self, query, chat_history=None):
        """재시도 로직이 포함된 Agent 실행 메서드."""
        last_error = None

        for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
            try:
                logger.info("[Retry] 시도 %d/%d", attempt, RETRY_MAX_ATTEMPTS)
                result = self.agent_executor.invoke({
                    "input": query,
                    "chat_history": chat_history or [],
                })
                return result
            except Exception as exc:
                last_error = exc
                logger.warning("[Retry] 시도 %d 실패: %s", attempt, exc)
                if attempt < RETRY_MAX_ATTEMPTS:
                    time.sleep(RETRY_DELAY_SECONDS)

        return {
            "output": f"죄송합니다. {RETRY_MAX_ATTEMPTS}회 재시도 후에도 처리에 실패했습니다. ({last_error})",
            "intermediate_steps": [],
        }

    def run(self, query, chat_history=None, use_cache=True):
        """사용자 질문을 처리하고 답변을 반환합니다."""
        start_time = time.time()

        logger.info("[ConnectHRAgent] 질문 수신: %s", query[:80])

        # ① 캐시 조회
        if use_cache:
            cached = response_cache.get(query)
            if cached is not None:
                cached["from_cache"] = True
                logger.info("[ConnectHRAgent] 캐시 응답 반환")
                return cached

        # ② Router로 경로 결정 (3단계 QueryRouter 사용)
        route = classify_route(query, router=self._router)

        # ③ 경로별 실행
        if route == "rag" and self.rag_chain is not None:
            # 비정형 문서 검색 경로
            try:
                answer = self.rag_chain.invoke(query)
                result = {
                    "output": answer,
                    "route": route,
                    "intermediate_steps": [],
                    "from_cache": False,
                }
            except Exception as exc:
                logger.warning("[ConnectHRAgent] RAG 체인 실행 실패, Agent로 폴백: %s", exc)
                result = self._run_with_retry(query, chat_history)
                result["route"] = "agent_fallback"
                result["from_cache"] = False
        elif self.agent_executor is not None:
            # DB 조회 또는 복합 경로 → Agent 실행
            result = self._run_with_retry(query, chat_history)
            result["route"] = route
            result["from_cache"] = False
        else:
            result = {
                "output": "죄송합니다. 에이전트 서비스를 사용할 수 없습니다.",
                "route": "error",
                "intermediate_steps": [],
                "from_cache": False,
            }

        # ④ 토큰 사용량 기록 (Ollama는 토큰 수를 반환하지 않으므로 추정)
        latency_ms = (time.time() - start_time) * 1000
        provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        if provider == "openai":
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        else:
            model = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")
        token_tracker.record(
            model=model,
            input_tokens=len(query.split()) * 2,  # 추정값
            output_tokens=len(result["output"].split()) * 2,  # 추정값
            operation="agent_run",
            latency_ms=latency_ms,
        )

        # ⑤ Langfuse 추적 전송
        langfuse_monitor.trace(
            name="agent_run",
            input_data=query,
            output_data=result["output"],
            metadata={"route": result["route"], "latency_ms": latency_ms},
        )

        # ⑥ 캐시 저장
        if use_cache:
            response_cache.set(query, result)

        logger.info(
            "[ConnectHRAgent] 처리 완료 (경로: %s, 소요: %.0fms)",
            result["route"],
            latency_ms,
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
