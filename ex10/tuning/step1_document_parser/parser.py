"""step1 — OCR 파싱과 Vision LLM 파싱 구현."""

import base64
import io
import os
from pathlib import Path

import fitz  # PyMuPDF
import httpx
import numpy as np
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
VISION_MODEL = os.getenv("VISION_MODEL", "qwen2.5vl:7b")
VISION_PROVIDER = os.getenv("VISION_PROVIDER", "ollama")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")
VISION_TIMEOUT = int(os.getenv("VISION_TIMEOUT", "600"))


# ---------------------------------------------------------------------------
# OCR 파싱
# ---------------------------------------------------------------------------

def parse_pdf_ocr(pdf_path: str | Path, dpi: int = 150) -> dict:
    """EasyOCR 기반 PDF 파싱. 페이지별 이미지를 OCR로 텍스트 추출한다."""
    import easyocr

    # TODO: EasyOCR Reader 생성 (한국어+영어, GPU 비활성)
    # TODO: PDF를 페이지별로 순회하며:
    #   1) 페이지를 이미지로 렌더링 (get_pixmap)
    #   2) PIL Image → numpy array 변환
    #   3) reader.readtext로 OCR 수행
    #   4) 결과 텍스트를 리스트에 수집
    # TODO: {"text": 전체 텍스트} 반환
    reader = easyocr.Reader(["ko", "en"], gpu=False)
    doc = fitz.open(str(pdf_path))
    page_texts = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=dpi)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        img_array = np.array(img)
        ocr_results = reader.readtext(img_array, detail=0)
        page_texts.append("\n".join(ocr_results))

    doc.close()
    return {"text": "\n\n".join(page_texts)}


# ---------------------------------------------------------------------------
# Vision LLM 파싱
# ---------------------------------------------------------------------------

def parse_pdf_vllm(pdf_path: str | Path, dpi: int = 150) -> dict:
    """Vision LLM 기반 PDF 파싱. 페이지 이미지를 LLM에게 보내 텍스트를 추출한다."""
    # TODO: PDF를 페이지별로 순회하며:
    #   1) 페이지를 PNG로 렌더링/저장
    #   2) _call_vision_llm으로 이미지 분석
    #   3) 임시 이미지 파일 삭제
    #   4) 결과 텍스트를 리스트에 수집
    # TODO: {"text": 전체 텍스트} 반환
    doc = fitz.open(str(pdf_path))
    page_texts = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=dpi)
        img_path = f"_vllm_page_{page_num + 1}.png"
        pix.save(img_path)

        caption = _call_vision_llm(img_path)
        page_texts.append(caption)

        Path(img_path).unlink(missing_ok=True)

    doc.close()
    return {"text": "\n\n".join(page_texts)}


# ---------------------------------------------------------------------------
# Vision LLM 호출 (Ollama / OpenAI)
# ---------------------------------------------------------------------------

def _call_vision_llm(image_path: str) -> str:
    """이미지를 Vision LLM에 전달하고 분석 결과를 받는다."""
    # TODO: 이미지를 base64 인코딩
    # TODO: VISION_PROVIDER에 따라 Ollama 또는 OpenAI 호출
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    if VISION_PROVIDER == "openai":
        return _call_openai_vision(img_b64)
    return _call_ollama_vision(img_b64)


def _call_ollama_vision(img_b64: str) -> str:
    """Ollama Vision API를 호출한다."""
    # TODO: OLLAMA_BASE_URL/api/generate 엔드포인트에 POST
    # TODO: model, prompt(문서 분석 지시), images 전달
    # TODO: 응답에서 response 텍스트 추출
    # TODO: 실패 시 에러 메시지 문자열 반환
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
    # TODO: OpenAI Chat Completions API에 POST
    # TODO: text + image_url(base64) 멀티모달 메시지 전달
    # TODO: 응답에서 content 텍스트 추출
    # TODO: 실패 시 에러 메시지 문자열 반환
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
