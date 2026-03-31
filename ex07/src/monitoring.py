"""ex07 구조화된 로깅 및 Langfuse 모니터링."""

import json
import logging
import os
import time
from datetime import datetime, timezone


# --- JSON 구조화 로그 포맷터 ---
class JsonFormatter(logging.Formatter):
    """로그 레코드를 JSON 형식으로 직렬화하는 포맷터."""

    def __init__(self, fmt_keys=None):
        """JsonFormatter를 초기화합니다."""
        super().__init__()
        self.fmt_keys = fmt_keys or []

    def format(self, record):
        """LogRecord를 JSON 문자열로 변환합니다."""
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 추가 필드 포함
        for key in self.fmt_keys:
            if hasattr(record, key):
                log_obj[key] = getattr(record, key)

        # exc_info가 있으면 포함
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj, ensure_ascii=False)


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
        cost_table = self.COST_PER_1K_TOKENS.get(model, {"input": 0.0, "output": 0.0})
        cost_usd = (
            (input_tokens / 1000 * cost_table["input"])
            + (output_tokens / 1000 * cost_table["output"])
        )

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "operation": operation,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": round(cost_usd, 6),
            "latency_ms": round(latency_ms, 2),
        }

        self._records.append(record)
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens

        self._logger.info(
            "[TokenTracker] 사용량 기록: model=%s, input=%d, output=%d, cost=$%.6f, latency=%.0fms",
            model, input_tokens, output_tokens, cost_usd, latency_ms,
        )

    def summary(self):
        """누적 토큰 사용량 요약을 반환합니다."""
        total_cost = sum(r["cost_usd"] for r in self._records)
        avg_latency = (
            sum(r["latency_ms"] for r in self._records) / len(self._records)
            if self._records
            else 0.0
        )
        return {
            "total_calls": len(self._records),
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
            "total_cost_usd": round(total_cost, 6),
            "avg_latency_ms": round(avg_latency, 2),
        }

    def recent(self, n=5):
        """최근 n개의 호출 기록을 반환합니다."""
        return self._records[-n:]


# --- Langfuse 래퍼 ---
class LangfuseMonitor:
    """Langfuse LLM 모니터링 도구 연동 래퍼."""

    def __init__(self):
        """LangfuseMonitor를 초기화합니다."""
        self._logger = logging.getLogger(__name__)
        self.enabled = False
        self._client = None
        self._init_langfuse()

    def _init_langfuse(self):
        """Langfuse 클라이언트를 초기화합니다."""
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")

        if not public_key or not secret_key:
            self._logger.info(
                "[Langfuse] LANGFUSE_PUBLIC_KEY 또는 LANGFUSE_SECRET_KEY가 설정되지 않았습니다. "
                "모니터링을 사용하려면 .env에 키를 추가하십시오."
            )
            return

        try:
            from langfuse import Langfuse

            self._client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            )
            self.enabled = True
            self._logger.info("[Langfuse] 모니터링 활성화됨")
        except ImportError:
            self._logger.info(
                "[Langfuse] langfuse 패키지가 설치되지 않았습니다. "
                "설치하려면: pip install langfuse"
            )

    def trace(self, name, input_data, output_data, metadata=None):
        """LLM 호출 추적 기록을 Langfuse에 전송합니다."""
        if not self.enabled or self._client is None:
            return

        try:
            self._client.trace(
                name=name,
                input=input_data if isinstance(input_data, str) else str(input_data),
                output=output_data if isinstance(output_data, str) else str(output_data),
                metadata=metadata or {},
            )
            self._logger.debug("[Langfuse] 추적 전송 완료: %s", name)
        except Exception as exc:
            self._logger.warning("[Langfuse] 추적 전송 실패: %s", exc)

    def flush(self):
        """대기 중인 Langfuse 이벤트를 즉시 전송합니다."""
        if not self.enabled or self._client is None:
            return
        try:
            self._client.flush()
        except Exception as exc:
            self._logger.warning("[Langfuse] flush 실패: %s", exc)


# --- 싱글톤 인스턴스 ---
token_tracker = TokenTracker()
langfuse_monitor = LangfuseMonitor()
