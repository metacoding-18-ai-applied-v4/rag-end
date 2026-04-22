"""ex11 — PDF 페이지를 PNG로 렌더링해 답변 근거로 제공.

답변 top-1 문서의 (source, page)를 받아 `data/docs/`에서 PDF를 찾고,
해당 페이지를 PNG로 렌더링해 `static/evidence/`에 캐시한 뒤,
채팅 UI에서 표시할 URL(`/static/evidence/*.png`)을 돌려준다.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "data" / "docs"
CACHE_DIR = BASE_DIR / "static" / "evidence"


def render_evidence_image(source_name: str, page_num: int, dpi: int = 150) -> str:
    """PDF 특정 페이지를 PNG로 렌더링하고 `/static/evidence/*.png` 경로를 반환한다.

    - source_name: 확장자를 제외한 PDF 파일 stem (예: `"HR_취업규칙_v1.0"`)
    - page_num: 1부터 시작하는 페이지 번호
    - dpi: 렌더링 해상도 (기본 150)
    - 이미 캐시돼 있으면 재사용한다. 없으면 새로 렌더링해 저장.
    - PDF를 찾지 못하면 빈 문자열 반환.
    """
    # 1. PDF 경로 탐색 (data/docs/ 하위 재귀)
    pdf_path = next(DOCS_DIR.rglob(f"{source_name}.pdf"), None)
    if not pdf_path:
        return ""

    # 2. 캐시 디렉토리 준비
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CACHE_DIR / f"{source_name}_p{page_num}.png"

    # 3. 이미 렌더링된 이미지면 재사용
    if out_path.exists():
        return f"/static/evidence/{out_path.name}"

    # 4. PDF 열어서 해당 페이지만 PNG로 저장
    try:
        doc = fitz.open(str(pdf_path))
        if page_num < 1 or page_num > len(doc):
            doc.close()
            return ""
        page = doc[page_num - 1]
        pix = page.get_pixmap(dpi=dpi)
        pix.save(str(out_path))
        doc.close()
    except Exception:
        return ""

    return f"/static/evidence/{out_path.name}"


def clear_cache() -> int:
    """캐시된 근거 이미지를 전부 삭제한다. 삭제한 파일 개수를 반환."""
    if not CACHE_DIR.exists():
        return 0
    count = 0
    for path in CACHE_DIR.glob("*.png"):
        path.unlink()
        count += 1
    return count
