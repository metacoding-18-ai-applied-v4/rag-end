"""agent_config.py 보조 함수 — 완성 코드."""

import logging
import time

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

logger = logging.getLogger(__name__)

# 설정 상수 (agent_config.py와 동일)
AGENT_MAX_ITERATIONS = 10
AGENT_TIMEOUT_SECONDS = 60
RETRY_MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 2.0


def build_agent_executor(llm, tools, system_prompt):
    """AgentExecutor를 구성합니다."""
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])
        agent = create_tool_calling_agent(llm, tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            max_iterations=AGENT_MAX_ITERATIONS,
            max_execution_time=AGENT_TIMEOUT_SECONDS,
            return_intermediate_steps=True,
            verbose=False,
        )
    except Exception as exc:
        logger.error("[ConnectHRAgent] AgentExecutor 구성 실패: %s", exc)
        return None


def run_with_retry(agent_executor, query, chat_history=None):
    """재시도 로직이 포함된 Agent 실행 메서드."""
    last_error = None
    for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
        try:
            result = agent_executor.invoke({
                "input": query,
                "chat_history": chat_history or [],
            })
            return result
        except Exception as exc:
            last_error = exc
            logger.warning(
                "[ConnectHRAgent] 시도 %d/%d 실패: %s",
                attempt, RETRY_MAX_ATTEMPTS, exc,
            )
            if attempt < RETRY_MAX_ATTEMPTS:
                time.sleep(RETRY_DELAY_SECONDS)

    return {"output": f"처리 중 오류가 발생했습니다: {last_error}"}
