"""ex07 — LLM 인스턴스 생성."""

import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# agent_config.py의 설정 상수 참조
AGENT_TIMEOUT_SECONDS = 60
RETRY_MAX_ATTEMPTS = 3


def build_llm():
    """환경 변수 기반으로 LLM 객체를 생성합니다."""
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    logger.info("[llm_factory] LLM 제공자: %s", provider)

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            print("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
            print(".env 파일에 OPENAI_API_KEY를 입력하십시오. (.env.example 참조)")
            sys.exit(1)

        try:
            from langchain_openai import ChatOpenAI

            model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            temperature = 1 if model_name.startswith("o") else 0
            llm = ChatOpenAI(
                model=model_name,
                openai_api_key=api_key,
                temperature=temperature,
                timeout=AGENT_TIMEOUT_SECONDS,
                max_retries=RETRY_MAX_ATTEMPTS,
            )
            logger.info("[llm_factory] OpenAI LLM 생성 완료: %s", model_name)
            return llm
        except ImportError:
            print("langchain-openai 패키지가 설치되지 않았습니다.")
            print("설치 명령: pip install langchain-openai")
            sys.exit(1)

    else:
        # Ollama (기본값)
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model_name = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")

        try:
            from langchain_ollama import ChatOllama

            llm = ChatOllama(
                base_url=ollama_url,
                model=model_name,
                timeout=AGENT_TIMEOUT_SECONDS,
            )
            logger.info("[llm_factory] Ollama LLM 생성 완료: %s (URL: %s)", model_name, ollama_url)
            return llm
        except ImportError:
            print("langchain-ollama 패키지가 설치되지 않았습니다.")
            print("설치 명령: pip install langchain-ollama")
            sys.exit(1)
        except Exception as exc:
            print(f"Ollama LLM 초기화 실패: {exc}")
            print(f"Ollama 서버({ollama_url})가 실행 중인지 확인하십시오. (명령: ollama serve)")
            sys.exit(1)
