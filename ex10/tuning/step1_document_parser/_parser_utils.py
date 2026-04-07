"""step1 — 파서 보조 함수 (완성 코드).

Vision LLM 호출, 이미지 인코딩 등 보조 로직을 제공한다.
"""

import base64
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
VISION_MODEL = os.getenv("VISION_MODEL", "qwen2.5vl:7b")
VISION_PROVIDER = os.getenv("VISION_PROVIDER", "ollama")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")
VISION_TIMEOUT = int(os.getenv("VISION_TIMEOUT", "600"))


def call_vision_llm(image_path: str) -> str:
    """이미지를 Vision LLM에 전달하고 분석 결과를 받는다."""
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    if VISION_PROVIDER == "openai":
        return _call_openai_vision(img_b64)
    return _call_ollama_vision(img_b64)


def _call_ollama_vision(img_b64: str) -> str:
    """Ollama Vision API를 호출한다."""
    try:
        resp = httpx.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": VISION_MODEL,
                "prompt": (
                    "이 문서 이미지를 분석하세요. "
                    "모든 텍스트, 표, 차트를 추출하고 "
                    "구조화된 Markdown 형식으로 출력하세요."
                ),
                "images": [img_b64],
                "stream": False,
            },
            timeout=float(VISION_TIMEOUT),
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        return f"[Ollama Vision 실패: {str(e)[:80]}]"


def _call_openai_vision(img_b64: str) -> str:
    """OpenAI Vision API를 fallback으로 호출한다."""
    try:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "이 문서 이미지를 분석하세요. "
                                    "모든 텍스트, 표, 차트를 추출하고 "
                                    "구조화된 Markdown 형식으로 출력하세요."
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_b64}",
                                },
                            },
                        ],
                    }
                ],
                "max_tokens": 2000,
            },
            timeout=float(VISION_TIMEOUT),
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[OpenAI Vision 실패: {str(e)[:80]}]"
