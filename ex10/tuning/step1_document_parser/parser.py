"""step1 — OCR 파싱과 Vision LLM 파싱 구현."""

import io
from pathlib import Path

import fitz  # PyMuPDF
import numpy as np
from PIL import Image

from ._parser_utils import call_vision_llm


# ---------------------------------------------------------------------------
# OCR 파싱
# ---------------------------------------------------------------------------

def parse_pdf_ocr(pdf_path: str | Path, dpi: int = 150) -> dict:
    """EasyOCR 기반 PDF 파싱. 페이지별 이미지를 OCR로 텍스트 추출한다."""
    import easyocr

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
    doc = fitz.open(str(pdf_path))
    page_texts = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=dpi)
        img_path = f"_vllm_page_{page_num + 1}.png"
        pix.save(img_path)

        caption = call_vision_llm(img_path)
        page_texts.append(caption)

        Path(img_path).unlink(missing_ok=True)

    doc.close()
    return {"text": "\n\n".join(page_texts)}
