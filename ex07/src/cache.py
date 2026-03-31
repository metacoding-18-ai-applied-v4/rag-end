"""ex07 응답 캐시 및 임베딩 캐시."""

import hashlib
import json
import logging
import os
import pickle
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# --- 기본 설정 상수 ---
DEFAULT_RESPONSE_TTL = 3600        # 응답 캐시 TTL (초): 1시간
DEFAULT_EMBEDDING_CACHE_DIR = "./outputs/embedding_cache"
DEFAULT_RESPONSE_CACHE_MAX_SIZE = 1000  # 최대 캐시 항목 수


class ResponseCache:
    """TTL 기반 인메모리 응답 캐시."""

    def __init__(self, ttl=DEFAULT_RESPONSE_TTL, max_size=DEFAULT_RESPONSE_CACHE_MAX_SIZE):
        """ResponseCache를 초기화합니다."""
        self.ttl = ttl
        self.max_size = max_size
        self._store = {}
        self._hits = 0
        self._misses = 0
        logger.info("[ResponseCache] 초기화 완료 (TTL: %d초, 최대 크기: %d)", ttl, max_size)

    def _make_key(self, query, context=""):
        """쿼리와 컨텍스트로 캐시 키를 생성합니다."""
        raw = f"{query}::{context}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, query, context=""):
        """캐시에서 응답을 조회합니다."""
        key = self._make_key(query, context)

        entry = self._store.get(key)
        if entry is None:
            self._misses += 1
            logger.debug("[ResponseCache] 미스: key=%s...", key[:12])
            return None

        value, expires_at = entry
        if time.time() > expires_at:
            # 만료된 항목 제거
            del self._store[key]
            self._misses += 1
            logger.debug("[ResponseCache] 만료: key=%s...", key[:12])
            return None

        self._hits += 1
        logger.info("[ResponseCache] 적중: key=%s... (잔여 TTL: %.0f초)", key[:12], expires_at - time.time())

        return value

    def set(self, query, value, context=""):
        """캐시에 응답을 저장합니다."""
        key = self._make_key(query, context)

        # 최대 크기 초과 시 가장 오래된 항목 제거
        if len(self._store) >= self.max_size:
            oldest_key = min(self._store, key=lambda k: self._store[k][1])
            del self._store[oldest_key]
            logger.debug("[ResponseCache] 최대 크기 초과로 항목 제거: key=%s...", oldest_key[:12])

        expires_at = time.time() + self.ttl
        self._store[key] = (value, expires_at)

        logger.info("[ResponseCache] 저장: key=%s... (만료: %.0f초 후)", key[:12], self.ttl)

    def clear(self):
        """만료된 캐시 항목을 제거합니다."""
        now = time.time()
        expired_keys = [k for k, (_, exp) in self._store.items() if now > exp]
        for key in expired_keys:
            del self._store[key]
        logger.info("[ResponseCache] 만료 항목 %d개 제거", len(expired_keys))
        return len(expired_keys)

    def stats(self):
        """캐시 통계를 반환합니다."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        return {
            "total_items": len(self._store),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2),
            "ttl_seconds": self.ttl,
            "max_size": self.max_size,
        }


class EmbeddingCache:
    """로컬 파일 기반 임베딩 캐시."""

    def __init__(self, cache_dir=DEFAULT_EMBEDDING_CACHE_DIR):
        """EmbeddingCache를 초기화합니다."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._hits = 0
        self._misses = 0
        logger.info("[EmbeddingCache] 초기화 완료 (캐시 디렉토리: %s)", self.cache_dir)

    def _make_cache_path(self, text):
        """텍스트로부터 캐시 파일 경로를 생성합니다."""
        key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{key}.pkl"

    def get(self, text):
        """캐시에서 임베딩 벡터를 조회합니다."""
        cache_path = self._make_cache_path(text)

        if not cache_path.exists():
            self._misses += 1
            logger.debug("[EmbeddingCache] 미스: %s", cache_path.name[:16])
            return None

        try:
            with open(cache_path, "rb") as f:
                embedding = pickle.load(f)
            self._hits += 1
            logger.debug("[EmbeddingCache] 적중: %s", cache_path.name[:16])
            return embedding
        except (pickle.UnpicklingError, EOFError) as exc:
            logger.warning("[EmbeddingCache] 캐시 파일 손상, 삭제: %s (%s)", cache_path.name, exc)
            cache_path.unlink(missing_ok=True)
            self._misses += 1
            return None

    def set(self, text, embedding):
        """캐시에 임베딩 벡터를 저장합니다."""
        cache_path = self._make_cache_path(text)

        try:
            with open(cache_path, "wb") as f:
                pickle.dump(embedding, f)
            logger.debug("[EmbeddingCache] 저장: %s (%d dims)", cache_path.name[:16], len(embedding))
        except OSError as exc:
            logger.error("[EmbeddingCache] 저장 실패: %s", exc)
            raise

    def stats(self):
        """캐시 통계를 반환합니다."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        cached_files = list(self.cache_dir.glob("*.pkl"))
        total_size_mb = sum(f.stat().st_size for f in cached_files) / (1024 * 1024)

        return {
            "cache_dir": str(self.cache_dir),
            "cached_items": len(cached_files),
            "total_size_mb": round(total_size_mb, 2),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2),
        }


# --- 싱글톤 인스턴스 ---
response_cache = ResponseCache(
    ttl=int(os.getenv("CACHE_TTL", str(DEFAULT_RESPONSE_TTL))),
    max_size=int(os.getenv("CACHE_MAX_SIZE", str(DEFAULT_RESPONSE_CACHE_MAX_SIZE))),
)

