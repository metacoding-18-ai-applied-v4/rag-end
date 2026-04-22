"""챕터 10 — PDF 하이브리드 파서 (pypdf → Vision LLM 폴백).

페이지별로 pypdf 텍스트 레이어를 먼저 뽑고, 길이가 `MIN_TEXT_LENGTH`
미만이면 스캔본으로 보고 Vision LLM에 넘긴다. 벡터DB 인덱싱 시 1회만
돌며, 이후 질의 단계에서는 다시 호출되지 않는다.

외부 의존은 Ollama Vision(기본 `qwen2.5vl:7b`)이다. 환경 변수 `VISION_MODEL`·
`OLLAMA_BASE_URL`로 교체 가능.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

import fitz  # PyMuPDF
import httpx

MIN_TEXT_LENGTH = 50
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
VISION_MODEL = os.getenv("VISION_MODEL", "qwen2.5vl:7b")
VISION_TIMEOUT = int(os.getenv("VISION_TIMEOUT", "600"))


def _vision_page(page: fitz.Page, dpi: int = 100) -> str:
    """페이지를 PNG로 렌더링해 Ollama Vision에 넘기고 텍스트를 받는다."""
    try:
        pix = page.get_pixmap(dpi=dpi)
        img_b64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")
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
        return (resp.json().get("response") or "").strip()
    except Exception:
        return ""


def parse_pdf_hybrid(pdf_path: str | Path) -> list[tuple[str, int, str]]:
    """PDF를 페이지별로 파싱해 `(텍스트, 페이지번호, 전략)` 리스트로 돌려준다.

    전략은 `text_layer`(pypdf) 또는 `vision`(Ollama Vision 폴백).
    """
    doc = fitz.open(str(pdf_path))
    results: list[tuple[str, int, str]] = []
    try:
        for page_num, page in enumerate(doc, start=1):
            text = (page.get_text() or "").strip()
            if len(text) >= MIN_TEXT_LENGTH:
                results.append((text, page_num, "text_layer"))
                continue
            vision_text = _vision_page(page)
            if vision_text:
                results.append((vision_text, page_num, "vision"))
    finally:
        doc.close()
    return results
