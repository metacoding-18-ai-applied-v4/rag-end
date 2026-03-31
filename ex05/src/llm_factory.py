"""ex05 — LLM 인스턴스 팩토리."""

import os

from dotenv import load_dotenv

load_dotenv()


def build_llm(temperature=0.1):
    """.env의 LLM_PROVIDER 값에 따라 LLM 인스턴스를 생성하여 반환한다."""
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "deepseek-r1:8b"),
            temperature=temperature,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=temperature,
        )
    else:
        raise ValueError(
            f"지원하지 않는 LLM_PROVIDER입니다: '{provider}'. "
            "ollama 또는 openai 중 하나를 선택하세요."
        )
