"""ex07 구조화된 로깅 및 Langfuse 모니터링."""

import logging
import os
import time
from datetime import datetime, timezone

from rich.table import Table

from ._monitoring_utils import (
    format_json_record,
    calculate_cost,
    token_summary,
    token_recent,
    init_langfuse,
    langfuse_trace,
    langfuse_flush,
)
from ._rich_logging import console


# --- JSON 구조화 로그 포맷터 ---
class JsonFormatter(logging.Formatter):
    """로그 레코드를 JSON 형식으로 직렬화하는 포맷터."""

    def __init__(self, fmt_keys=None):
        """JsonFormatter를 초기화합니다."""
        super().__init__()
        self.fmt_keys = fmt_keys or []

    def format(self, record):
        """LogRecord를 JSON 문자열로 변환합니다."""
        return format_json_record(record, self.fmt_keys)


def setup_logging(level="INFO", use_json=True, log_file=None):
    """애플리케이션 로깅 시스템을 설정합니다."""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"유효하지 않은 로그 레벨입니다: '{level}'. INFO, DEBUG, WARNING, ERROR 중 하나를 사용하십시오.")

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # 기존 핸들러 제거
    root_logger.handlers.clear()

    # 포맷터 선택
    if use_json:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 파일 핸들러 (선택사항)
    if log_file:
        log_path = os.path.dirname(log_file)
        if log_path:
            os.makedirs(log_path, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        logging.getLogger(__name__).info("로그 파일 저장 경로: %s", log_file)

    logging.getLogger(__name__).info(
        "로깅 설정 완료 (레벨: %s, JSON: %s)", level, use_json
    )


# --- 토큰 사용량 추적기 ---
class TokenTracker:
    """LLM API 호출별 토큰 사용량을 추적합니다."""

    # 간략한 비용 기준 (달러/1000토큰, 참고용)
    COST_PER_1K_TOKENS = {
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "deepseek-r1:8b": {"input": 0.0, "output": 0.0},  # 로컬 모델: 무료
        "llama3.1:8b": {"input": 0.0, "output": 0.0},  # 로컬 모델: 무료
    }

    def __init__(self):
        """TokenTracker를 초기화합니다."""
        self._records = []
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._logger = logging.getLogger(__name__)

    def record(self, model, input_tokens, output_tokens, operation="chat", latency_ms=0.0):
        """토큰 사용량을 기록합니다."""
        # TODO: record — 호출별 토큰·비용·지연 누적
        cost_usd = calculate_cost(model, input_tokens, output_tokens, self.COST_PER_1K_TOKENS)

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "operation": operation,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": cost_usd,
            "latency_ms": round(latency_ms, 2),
        }

        self._records.append(record)
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens

        self._logger.info(
            "[TokenTracker] 사용량 기록: model=%s, input=%d, output=%d, cost=$%.6f, latency=%.0fms",
            model, input_tokens, output_tokens, cost_usd, latency_ms,
        )

        # Rich Table로 호출별 요약 출력 — 라벨 12자 폭 고정으로 값 컬럼이 세로 정렬
        table = Table(
            title="TokenTracker 기록",
            title_style="bold cyan",
            title_justify="left",
            show_header=False,
            box=None,
            pad_edge=False,
            padding=(0, 1),
        )
        table.add_column(style="dim", width=12, no_wrap=True)
        table.add_column(style="bold")
        table.add_row("모델", model)
        table.add_row("입력 토큰", f"{input_tokens:,}")
        table.add_row("출력 토큰", f"{output_tokens:,}")
        table.add_row("비용 (USD)", f"${cost_usd:.6f}")
        table.add_row("지연 시간", f"{latency_ms:.0f} ms")
        console.print(table)

    def summary(self):
        """누적 토큰 사용량 요약을 반환합니다."""
        return token_summary(self)

    def recent(self, n=5):
        """최근 n개의 호출 기록을 반환합니다."""
        return token_recent(self, n)


# --- Langfuse 래퍼 ---
class LangfuseMonitor:
    """Langfuse LLM 모니터링 도구 연동 래퍼."""

    def __init__(self):
        """LangfuseMonitor를 초기화합니다."""
        self._logger = logging.getLogger(__name__)
        self.enabled = False
        self._client = None
        init_langfuse(self)

    def trace(self, name, input_data, output_data, metadata=None):
        """LLM 호출 추적 기록을 Langfuse에 전송합니다."""
        langfuse_trace(self, name, input_data, output_data, metadata)

    def flush(self):
        """대기 중인 Langfuse 이벤트를 즉시 전송합니다."""
        langfuse_flush(self)


# --- 싱글톤 인스턴스 ---
token_tracker = TokenTracker()
langfuse_monitor = LangfuseMonitor()
