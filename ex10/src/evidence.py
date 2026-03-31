"""ex10 src — 답변 근거 이미지 경로 해석 유틸리티.

캡처된 이미지의 절대 경로를 웹 서빙용 상대 URL로 변환하고,
캡처 디렉토리의 이미지 목록을 반환한다.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CAPTURED_DIR = BASE_DIR / "data" / "captured"


def resolve_image_url(image_path: str) -> str:
    """캡처 이미지의 절대 경로를 웹 URL로 변환한다.

    Args:
        image_path: 캡처된 이미지의 절대 경로.

    Returns:
        웹 서빙용 상대 URL (예: /captured/pdf/doc_page_1.png).
        변환 불가 시 빈 문자열.
    """
    captured_str = str(CAPTURED_DIR)

    if captured_str in image_path:
        relative = image_path.split("captured" + os.sep, 1)[-1]
        return f"/captured/{relative}"

    if image_path.startswith("/captured/"):
        return image_path

    return ""


def list_captured_images() -> list[dict]:
    """캡처 디렉토리의 모든 PNG 이미지 목록을 반환한다.

    Returns:
        이미지 정보 리스트. 각 항목에 format, filename, size_kb, web_url 포함.
    """
    images = []

    if not CAPTURED_DIR.exists():
        return images

    for sub_dir in sorted(CAPTURED_DIR.iterdir()):
        if not sub_dir.is_dir():
            continue

        fmt = sub_dir.name.upper()

        for img in sorted(sub_dir.glob("*.png")):
            size_kb = img.stat().st_size / 1024
            web_url = resolve_image_url(str(img))
            images.append({
                "format": fmt,
                "filename": img.name,
                "size_kb": round(size_kb, 1),
                "web_url": web_url,
            })

    return images
