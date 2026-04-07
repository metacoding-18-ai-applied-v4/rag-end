"""monitoring.py 보조 함수 — 완성 코드."""

import json
import logging
import os
import time
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


# ── JsonFormatter ────────────────────────────────────────────

def format_json_record(record, fmt_keys):
    """LogRecord를 JSON 딕셔너리 문자열로 변환합니다."""
    log_dict = {
        "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
        "level": record.levelname,
        "logger": record.name,
        "message": record.getMessage(),
    }
    for key in fmt_keys:
        if hasattr(record, key):
            log_dict[key] = getattr(record, key)
    if record.exc_info and record.exc_info[0] is not None:
        log_dict["exception"] = logging.Formatter().formatException(record.exc_info)
    return json.dumps(log_dict, ensure_ascii=False)


# ── TokenTracker 보조 ────────────────────────────────────────

def calculate_cost(model, input_tokens, output_tokens, cost_table):
    """모델별 비용을 계산합니다."""
    rates = cost_table.get(model, {"input": 0.0, "output": 0.0})
    input_cost = (input_tokens / 1000) * rates["input"]
    output_cost = (output_tokens / 1000) * rates["output"]
    return round(input_cost + output_cost, 6)


def token_summary(tracker):
    """누적 토큰 사용량 요약을 딕셔너리로 반환합니다."""
    total_cost = sum(r.get("cost_usd", 0.0) for r in tracker._records)
    avg_latency = (
        sum(r.get("latency_ms", 0.0) for r in tracker._records) / len(tracker._records)
        if tracker._records
        else 0.0
    )
    return {
        "total_calls": len(tracker._records),
        "total_input_tokens": tracker._total_input_tokens,
        "total_output_tokens": tracker._total_output_tokens,
        "total_cost_usd": round(total_cost, 6),
        "avg_latency_ms": round(avg_latency, 1),
    }


def token_recent(tracker, n=5):
    """최근 n개의 호출 기록을 반환합니다."""
    return tracker._records[-n:]


# ── LangfuseMonitor ──────────────────────────────────────────

def init_langfuse(monitor):
    """Langfuse 클라이언트를 초기화합니다."""
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    if not public_key or not secret_key:
        monitor._logger.info("[Langfuse] 환경변수 미설정 — 모니터링 비활성")
        return
    try:
        from langfuse import Langfuse
        monitor._client = Langfuse(public_key=public_key, secret_key=secret_key)
        monitor.enabled = True
        monitor._logger.info("[Langfuse] 클라이언트 초기화 완료")
    except ImportError:
        monitor._logger.info("[Langfuse] langfuse 패키지 미설치 — 모니터링 비활성")


def langfuse_trace(monitor, name, input_data, output_data, metadata=None):
    """LLM 호출 추적 기록을 Langfuse에 전송합니다."""
    if not monitor.enabled:
        return
    try:
        monitor._client.trace(
            name=name,
            input=input_data,
            output=output_data,
            metadata=metadata or {},
        )
    except Exception as exc:
        monitor._logger.warning("[Langfuse] trace 전송 실패: %s", exc)


def langfuse_flush(monitor):
    """대기 중인 Langfuse 이벤트를 즉시 전송합니다."""
    if not monitor.enabled:
        return
    monitor._client.flush()
