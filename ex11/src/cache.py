"""ex07 응답 캐시 및 임베딩 캐시."""

import logging
import os
import time
from pathlib import Path

from ._cache_utils import (
    make_response_key,
    response_cache_stats,
    response_cache_clear,
    embedding_get,
    embedding_set,
    embedding_cache_stats,
)

logger = logging.getLogger(__name__)

# --- 기본 설정 상수 ---
DEFAULT_RESPONSE_TTL = 3600        # 응답 캐시 TTL (초): 1시간
DEFAULT_EMBEDDING_CACHE_DIR = "./outputs/embedding_cache"
DEFAULT_RESPONSE_CACHE_MAX_SIZE = 1000  # 최대 캐시 항목 수


class ResponseCache:
    """TTL 기반 인메모리 응답 캐시."""

    def __init__(self, ttl=DEFAULT_RESPONSE_TTL, max_size=DEFAULT_RESPONSE_CACHE_MAX_SIZE):
        """ResponseCache를 초기화합니다."""
        # 1. TTL·max_size는 .env 또는 기본값에서 주입 (3600초, 1000개)
        self.ttl = ttl
        self.max_size = max_size
        # 2. 메모장 본체: key → (value, expires_at) 튜플
        self._store = {}
        # 3. 통계 카운터 — 운영 중 적중률을 보기 위한 값
        self._hits = 0
        self._misses = 0
        logger.info("[ResponseCache] 초기화 완료 (TTL: %d초, 최대 크기: %d)", ttl, max_size)

    def get(self, query, context=""):
        """캐시에서 응답을 조회합니다 (TTL 만료 체크)."""
        # TODO: get — TTL 검사 후 HIT/MISS 반환
        # 1. 질문(+문맥)을 SHA-256 해시로 변환해 고정 길이 키로
        key = make_response_key(query, context)

        # 2. 저장소에 키가 아예 없으면 MISS
        entry = self._store.get(key)
        if entry is None:
            self._misses += 1
            logger.debug("[ResponseCache] 미스: key=%s...", key[:12])
            return None

        # 3. 있더라도 만료 시각이 지났으면 삭제 후 MISS
        value, expires_at = entry
        if time.time() > expires_at:
            del self._store[key]
            self._misses += 1
            logger.debug("[ResponseCache] 만료: key=%s...", key[:12])
            return None

        # 4. 살아 있으면 HIT — 남은 TTL 로그로 남겨 디버깅 편하게
        self._hits += 1
        logger.info("[ResponseCache] 적중: key=%s... (잔여 TTL: %.0f초)", key[:12], expires_at - time.time())
        return value

    def set(self, query, value, context=""):
        """캐시에 응답을 저장합니다 (max_size 초과 시 오래된 항목 제거)."""
        # TODO: set — max_size 초과 시 가장 오래된 항목 제거
        # 1. 조회와 같은 방식으로 키 생성
        key = make_response_key(query, context)

        # 2. 용량 초과 시 만료 임박 항목 한 건 제거
        if len(self._store) >= self.max_size:
            oldest_key = min(self._store, key=lambda k: self._store[k][1])
            del self._store[oldest_key]
            logger.debug("[ResponseCache] 최대 크기 초과로 항목 제거: key=%s...", oldest_key[:12])

        # 3. 만료 시각 = 지금 + TTL. 튜플로 저장
        expires_at = time.time() + self.ttl
        self._store[key] = (value, expires_at)
        logger.info("[ResponseCache] 저장: key=%s... (만료: %.0f초 후)", key[:12], self.ttl)

    def clear(self):
        """만료된 캐시 항목을 제거합니다."""
        return response_cache_clear(self)

    def stats(self):
        """캐시 통계를 반환합니다."""
        return response_cache_stats(self)


class EmbeddingCache:
    """로컬 파일 기반 임베딩 캐시."""

    def __init__(self, cache_dir=DEFAULT_EMBEDDING_CACHE_DIR):
        """EmbeddingCache를 초기화합니다."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._hits = 0
        self._misses = 0
        logger.info("[EmbeddingCache] 초기화 완료 (캐시 디렉토리: %s)", self.cache_dir)

    def get_or_compute(self, text, compute_fn):
        """캐시 히트면 반환, 미스면 compute_fn으로 계산 후 저장합니다."""
        # TODO: get_or_compute — 캐시 히트면 반환, 미스면 계산 후 저장
        emb, hits_delta, misses_delta = embedding_get(self.cache_dir, text, None)
        self._hits += hits_delta
        self._misses += misses_delta

        if emb is not None:
            return emb

        emb = compute_fn(text)
        embedding_set(self.cache_dir, text, emb)
        return emb

    def stats(self):
        """캐시 통계를 반환합니다."""
        return embedding_cache_stats(self)


# --- 싱글톤 인스턴스 ---
response_cache = ResponseCache(
    ttl=int(os.getenv("CACHE_TTL", str(DEFAULT_RESPONSE_TTL))),
    max_size=int(os.getenv("CACHE_MAX_SIZE", str(DEFAULT_RESPONSE_CACHE_MAX_SIZE))),
)
