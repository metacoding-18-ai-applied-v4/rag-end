"""step2 — 하이브리드 파싱 전략 구현.

OCR 텍스트 길이가 임계값 미만이면 Vision LLM으로 전환한다.
텍스트 레이어 우선 전략도 제공한다.
"""

import os

import fitz  # PyMuPDF

from ._hybrid_utils import ocr_page, vision_page

MIN_TEXT_LENGTH = int(os.getenv("MIN_TEXT_LENGTH", "50"))


# ---------------------------------------------------------------------------
# 하이브리드 전략 1: OCR → Vision LLM fallback
# ---------------------------------------------------------------------------

def process_image_hybrid(
    page: fitz.Page,
    dpi: int = 150,
    threshold: int | None = None,
    vision_model: str | None = None,
) -> dict:
    """OCR 텍스트가 임계값 이상이면 OCR 결과를, 아니면 Vision LLM으로 전환한다."""
    threshold = threshold or MIN_TEXT_LENGTH

    ocr_text = ocr_page(page, dpi=dpi)
    ocr_len = len(ocr_text.strip())

    if ocr_len >= threshold:
        return {"strategy": "ocr", "text": ocr_text, "char_count": ocr_len}

    vision_text = vision_page(page, dpi=dpi, model=vision_model)
    return {
        "strategy": "vision",
        "text": vision_text or ocr_text,
        "char_count": len(vision_text) if vision_text else ocr_len,
    }


# ---------------------------------------------------------------------------
# 하이브리드 전략 2: 텍스트 레이어 → Vision LLM fallback
# ---------------------------------------------------------------------------

def process_image_textlayer(
    page: fitz.Page,
    dpi: int = 150,
    vision_model: str | None = None,
) -> dict:
    """PDF 텍스트 레이어가 있으면 사용, 없으면 Vision LLM으로 전환한다."""
    text_layer = page.get_text().strip()

    if text_layer:
        return {
            "strategy": "text_layer",
            "text": text_layer,
            "char_count": len(text_layer),
        }

    vision_text = vision_page(page, dpi=dpi, model=vision_model)
    return {
        "strategy": "vision",
        "text": vision_text,
        "char_count": len(vision_text) if vision_text else 0,
    }
