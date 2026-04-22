"""Rich 기반 콘솔 로깅 — 운영 로그 가독성 강화 (완성 코드)."""

import logging

from rich.console import Console
from rich.logging import RichHandler

# 싱글톤 콘솔 — 모든 모듈이 동일 인스턴스 재사용
# force_terminal: uvicorn이 stdout을 파이프로 연결해도 ANSI 색상 유지
console = Console(force_terminal=True, color_system="truecolor")


def setup_rich_logging(level=logging.INFO):
    """로깅 핸들러를 RichHandler로 교체하여 컬러 출력을 활성화합니다."""
    # 1. 기존 핸들러 제거 (basicConfig 중복 방지)
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)

    # 2. RichHandler 설치 — 시간·레벨·메시지 컬럼 정렬 유지
    #    omit_repeated_times=False: 매 줄에 timestamp 표시 → 컬럼이 나란히 떨어짐
    rich_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        show_path=False,
        markup=True,
        omit_repeated_times=False,
        log_time_format="[%H:%M:%S]",
    )
    rich_handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(rich_handler)
    root.setLevel(level)
