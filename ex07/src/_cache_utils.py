"""cache.py 보조 함수 — 완성 코드."""

import hashlib
import logging
import os
import pickle
import time
from pathlib import Path

logger = logging.getLogger(__name__)


# ── ResponseCache 보조 ──────────────────────────────────────

def make_response_key(query, context=""):
    """쿼리와 컨텍스트로 SHA-256 캐시 키를 생성합니다."""
    raw = f"{query}::{context}"
    return hashlib.sha256(raw.encode()).hexdigest()


def response_cache_stats(cache):
    """ResponseCache 통계를 딕셔너리로 반환합니다."""
    total = cache._hits + cache._misses
    return {
        "total_items": len(cache._store),
        "hits": cache._hits,
        "misses": cache._misses,
        "hit_rate_percent": round(cache._hits / total * 100, 1) if total else 0.0,
        "ttl_seconds": cache.ttl,
        "max_size": cache.max_size,
    }


def response_cache_clear(cache):
    """만료된 캐시 항목을 제거하고 삭제된 수를 반환합니다."""
    now = time.time()
    expired = [k for k, (_, exp) in cache._store.items() if exp <= now]
    for k in expired:
        del cache._store[k]
    if expired:
        logger.info("[ResponseCache] 만료 항목 %d개 제거", len(expired))
    return len(expired)


# ── EmbeddingCache 보조 ─────────────────────────────────────

def make_embedding_cache_path(cache_dir, text):
    """텍스트의 SHA-256 해시로 .pkl 파일 경로를 생성합니다."""
    h = hashlib.sha256(text.encode()).hexdigest()
    return cache_dir / f"{h}.pkl"


def embedding_get(cache_dir, text, hit_counter_ref):
    """캐시에서 임베딩 벡터를 조회합니다.

    Returns:
        (embedding, hits_delta, misses_delta)
    """
    path = make_embedding_cache_path(cache_dir, text)
    if not path.exists():
        return None, 0, 1
    try:
        with open(path, "rb") as f:
            emb = pickle.load(f)
        return emb, 1, 0
    except Exception:
        logger.warning("[EmbeddingCache] 손상된 캐시 파일 삭제: %s", path)
        path.unlink(missing_ok=True)
        return None, 0, 1


def embedding_set(cache_dir, text, embedding):
    """캐시에 임베딩 벡터를 저장합니다."""
    path = make_embedding_cache_path(cache_dir, text)
    with open(path, "wb") as f:
        pickle.dump(embedding, f)


def embedding_cache_stats(cache):
    """EmbeddingCache 통계를 딕셔너리로 반환합니다."""
    total_hits = cache._hits + cache._misses
    files = list(cache.cache_dir.glob("*.pkl"))
    total_size = sum(f.stat().st_size for f in files)
    return {
        "cache_dir": str(cache.cache_dir),
        "cached_items": len(files),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "hits": cache._hits,
        "misses": cache._misses,
        "hit_rate_percent": round(cache._hits / total_hits * 100, 1) if total_hits else 0.0,
    }
