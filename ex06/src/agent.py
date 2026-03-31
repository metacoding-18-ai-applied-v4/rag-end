"""ex06 — 통합 에이전트 모듈."""

from src.llm_factory import build_llm
from src.agent_helpers import (
    parse_agent_result,
    serialize_steps,
    clean_think_tags,
    fallback_response,
)
from src.mcp_tools import ALL_TOOLS
from src.router import QueryRouter


# ---------------------------------------------------------------------------
# 시스템 프롬프트
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """당신은 사내 HR 및 업무 질문에 답변하는 AI 어시스턴트입니다.

사용 가능한 도구:
- leave_balance: 직원 연차 잔여 조회 (emp_no 또는 이름으로 검색)
- sales_sum: 매출 합계 조회 (부서, 기간 필터 가능)
- list_employees: 직원 목록 조회 (부서 필터 가능)
- search_documents: 사내 문서 검색 (절차, 정책, 안내 등)

규칙:
1. 정형 데이터(숫자/통계/목록)는 DB 조회 도구를 사용하세요.
2. 비정형 질문(절차/정책/설명)은 search_documents를 사용하세요.
3. 복합 질문은 두 종류의 도구를 모두 사용하세요.
4. 답변은 반드시 한국어로 작성하세요.
5. 도구 실행 결과의 핵심 정보만 추출하여 자연스러운 문장으로 답변하세요. 원본 JSON이나 딕셔너리를 절대 그대로 출력하지 마세요."""


# ---------------------------------------------------------------------------
# 통합 에이전트 클래스
# ---------------------------------------------------------------------------

class IntegratedAgent:
    """정형 + 비정형 통합 ReAct 에이전트."""

    def __init__(self, llm=None):
        """에이전트를 초기화한다."""
        self._llm = llm or build_llm()
        self._router = QueryRouter(llm=self._llm)
        self._agent_executor = self._build_agent_executor()

    def _build_agent_executor(self):
        """LangChain AgentExecutor를 생성한다."""
        try:
            from langchain.agents import AgentExecutor, create_tool_calling_agent
            from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

            # ① 프롬프트 구성 (system + history + input + scratchpad)
            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])

            # ② Tool Calling Agent 생성
            agent = create_tool_calling_agent(
                llm=self._llm,
                tools=ALL_TOOLS,
                prompt=prompt,
            )

            # ③ AgentExecutor 래핑 (중간 단계 반환 활성화)
            return AgentExecutor(
                agent=agent,
                tools=ALL_TOOLS,
                verbose=False,
                return_intermediate_steps=True,
                max_iterations=10,
                handle_parsing_errors=True,
            )
        except Exception as e:
            print(f"[경고] AgentExecutor 초기화 실패: {e}. 폴백 모드로 동작합니다.")
            return None

    def run(self, query):
        """질문을 처리하고 통합 응답을 반환한다."""
        # ① 질문 유형 분류
        query_type = self._router.classify_query(query)  # ①

        # ② 에이전트 실행
        if self._agent_executor is None:
            return fallback_response(self._llm, query, query_type)

        try:
            result = self._agent_executor.invoke({"input": query})  # ②
            answer = result.get("output", "답변을 생성하지 못했습니다.")
            steps = result.get("intermediate_steps", [])

            # ③ DeepSeek-R1 <think> 태그 제거
            answer = clean_think_tags(answer)  # ③

            # ④ 중간 단계에서 정형/비정형 데이터 추출
            structured_data, unstructured_data = parse_agent_result(steps)  # ④

            return {
                "answer": answer,
                "query_type": query_type,
                "structured_data": structured_data,
                "unstructured_data": unstructured_data,
                "steps": serialize_steps(steps),
            }
        except Exception as e:
            return {
                "answer": f"처리 중 오류가 발생했습니다: {e}",
                "query_type": query_type,
                "structured_data": {},
                "unstructured_data": [],
                "steps": [],
            }
