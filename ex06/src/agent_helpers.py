"""ex06 — 에이전트 헬퍼 함수."""

import json
import re


def parse_agent_result(steps):
    """에이전트 중간 실행 단계에서 정형/비정형 데이터를 추출한다."""
    structured_data = {}
    unstructured_data = []

    for action, observation in steps:
        tool_name = getattr(action, "tool", "")

        if tool_name in ("leave_balance", "list_employees", "sales_sum"):
            if isinstance(observation, dict):
                structured_data[tool_name] = observation
            elif isinstance(observation, str):
                try:
                    structured_data[tool_name] = json.loads(observation)
                except json.JSONDecodeError:
                    structured_data[tool_name] = {"raw": observation}

        elif tool_name == "search_documents":
            if isinstance(observation, dict):
                docs = observation.get("results", [])
            elif isinstance(observation, str):
                try:
                    parsed = json.loads(observation)
                    docs = parsed.get("results", []) if isinstance(parsed, dict) else []
                except json.JSONDecodeError:
                    docs = []
            else:
                docs = []
            unstructured_data.extend(docs)

    return structured_data, unstructured_data


def serialize_steps(steps):
    """중간 단계를 JSON 직렬화 가능한 형태로 변환한다."""
    serialized = []
    for action, observation in steps:
        serialized.append({
            "tool": getattr(action, "tool", "unknown"),
            "input": getattr(action, "tool_input", {}),
            "output": observation if isinstance(observation, (str, int, float, bool)) else str(observation),
        })
    return serialized


def clean_think_tags(text):
    """DeepSeek-R1 <think> 태그를 제거한다."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def fallback_response(llm, query, query_type):
    """AgentExecutor 없을 때 직접 LLM 응답을 생성한다."""
    try:
        response = llm.invoke(f"다음 질문에 한국어로 답변하세요: {query}")
        answer = response.content if hasattr(response, "content") else str(response)
        answer = clean_think_tags(answer)
    except Exception as e:
        answer = f"LLM 응답 생성 실패: {e}"

    return {
        "answer": answer,
        "query_type": query_type,
        "structured_data": {},
        "unstructured_data": [],
        "steps": [],
    }
