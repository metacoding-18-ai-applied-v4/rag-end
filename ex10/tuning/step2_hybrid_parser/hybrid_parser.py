"""step2 — 하이브리드 파싱 전략 구현.

pypdf(fitz)가 의미 있는 양의 텍스트를 돌려주면 그대로 사용하고,
부족하면 Vision LLM으로 전환한다.
"""

import fitz  # PyMuPDF

from ._hybrid_utils import vision_page

# pypdf 텍스트 임계값.
# - 이 미만이면 스캔본이거나 축 레이블만 있는 차트 페이지로 간주하고 Vision으로 전환.
# - 일반 텍스트 페이지는 보통 수백~수천 자가 나오므로 50자 기준은 여유 있게 안전하다.
MIN_TEXT_LENGTH = 50


def process_page_hybrid(
    page: fitz.Page,
    dpi: int = 150,
    vision_model: str | None = None,
) -> dict:
    """pypdf 텍스트가 충분하면 text_layer, 부족하면 Vision LLM."""
    text = page.get_text().strip()
    if len(text) >= MIN_TEXT_LENGTH:
        return {"strategy": "text_layer", "text": text, "char_count": len(text)}

    vision_text = vision_page(page, dpi=dpi, model=vision_model)
    return {
        "strategy": "vision",
        "text": vision_text,
        "char_count": len(vision_text) if vision_text else 0,
    }
