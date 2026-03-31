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
    # TODO: CAPTURED_DIR 경로가 image_path에 포함되면 상대 경로 추출
    # TODO: /captured/ 접두사를 붙여 웹 URL로 변환
    # TODO: 이미 /captured/로 시작하면 그대로 반환
    # TODO: 변환 불가 시 빈 문자열 반환
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
    # TODO: CAPTURED_DIR 하위 디렉토리를 순회
    # TODO: 각 서브디렉토리의 PNG 파일에 대해:
    #   - format: 서브디렉토리명 (대문자)
    #   - filename: 파일명
    #   - size_kb: 파일 크기 (KB)
    #   - web_url: resolve_image_url 결과
    # TODO: images 리스트 반환
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
