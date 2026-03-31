"""ex10 src — PDF 페이지 캡처 + 텍스트 추출.

PDF를 페이지별 PNG 이미지로 렌더링하고 텍스트 레이어를 추출한다.
캡처된 이미지는 data/captured/pdf/ 에 저장된다.
"""

from pathlib import Path

import fitz  # PyMuPDF

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "data" / "docs"
CAPTURED_DIR = BASE_DIR / "data" / "captured" / "pdf"


def capture_pdf_pages(pdf_path: Path | str) -> list[dict]:
    """PDF를 페이지별 PNG로 캡처하고 텍스트를 추출한다.

    Args:
        pdf_path: PDF 파일 경로.

    Returns:
        페이지별 캡처 결과 리스트. 각 항목에 page, image_path, text, metadata 포함.
    """
    pdf_path = Path(pdf_path)
    CAPTURED_DIR.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    results = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        # 페이지를 PNG로 렌더링
        pix = page.get_pixmap(dpi=200)
        img_path = CAPTURED_DIR / f"{pdf_path.stem}_page_{page_num + 1}.png"
        pix.save(str(img_path))

        # 텍스트 레이어 추출
        text = page.get_text()

        results.append({
            "page": page_num + 1,
            "image_path": str(img_path),
            "text": text,
            "metadata": {
                "source": pdf_path.name,
                "image_path": str(img_path),
            },
        })

    doc.close()
    return results
