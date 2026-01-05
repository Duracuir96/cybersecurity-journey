# src/data/cache_manager.py

import json
import redis
import logging
from typing import Any, Optional
from datetime import timedelta, datetime

# ============================================================
# FALLBACK LOCAL CACHE
# ============================================================
local_cache = {}

def _now():
    return datetime.utcnow()


# ============================================================
# TRY REDIS
# ============================================================
REDIS_ENABLED = True

import os

REDIS_ENABLED = True

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB   = int(os.getenv("REDIS_DB", 0))

try:
    REDIS_POOL = redis.ConnectionPool(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        max_connections=20,
        decode_responses=True
    )
    redis_client = redis.Redis(connection_pool=REDIS_POOL)
    redis_client.ping()
    logging.info(f"Redis connected: {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    redis_client = None
    REDIS_ENABLED = False
    logging.warning(f"Redis disabled: {e}")


# ============================================================
# TTL
# ============================================================
TTL_ANALYTICS = 60 * 5
TTL_REPORTS   = 60 * 60 * 24


# ============================================================
# SET CACHE (safe)
# ============================================================
def set_cache(key: str, data: Any, ttl: Optional[int] = None) -> None:
    """
    Accept dict/list/string → convert to JSON internally.
    """

    try:
        serialized = json.dumps(data, default=str)
    except Exception as e:
        raise ValueError(f"Cache serialization error: {e}")

    # Redis
    if REDIS_ENABLED and redis_client:
        try:
            if ttl:
                redis_client.setex(key, timedelta(seconds=ttl), serialized)
            else:
                redis_client.set(key, serialized)
            return
        except Exception as e:
            logging.error(f"Redis error in set_cache: {e}")

    # Fallback local
    expires = _now() + timedelta(seconds=ttl) if ttl else None
    local_cache[key] = {"data": serialized, "expires": expires}


# ============================================================
# GET CACHE
# ============================================================
def get_cache(key: str) -> Optional[Any]:

    # Redis
    if REDIS_ENABLED and redis_client:
        try:
            raw = redis_client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as e:
            logging.error(f"Redis error in get_cache: {e}")

    # Local fallback
    item = local_cache.get(key)
    if not item:
        return None

    if item["expires"] and item["expires"] < _now():
        del local_cache[key]
        return None

    return json.loads(item["data"])


# ============================================================
# HELPERS: ANALYTICS + REPORTS
# ============================================================
def cache_analytics(key: str, data: Any) -> None:
    set_cache(key, data, TTL_ANALYTICS)

def cache_report(key: str, data: Any) -> None:
    set_cache(key, data, TTL_REPORTS)


# ============================================================
# INVALIDATION
# ============================================================
def invalidate(key: str) -> None:
    if REDIS_ENABLED and redis_client:
        try:
            redis_client.delete(key)
        except Exception:
            pass
    local_cache.pop(key, None)


def invalidate_prefix(prefix: str) -> None:
    pattern = f"{prefix}"

    if REDIS_ENABLED and redis_client:
        try:
            keys = redis_client.keys(pattern + "*")
            if keys:
                redis_client.delete(*keys)
        except Exception:
            pass

    for k in list(local_cache.keys()):
        if k.startswith(prefix):
            local_cache.pop(k, None)


def clear_all_cache() -> None:
    if REDIS_ENABLED and redis_client:
        try:
            redis_client.flushdb()
        except Exception:
            pass

    local_cache.clear()


# ============================================================
# KEY BUILDERS
# ============================================================
def key_analytics(product_id: str, days: int) -> str:
    return f"analytics:{product_id}:{days}"

def key_report(hash_key: str) -> str:
    return f"report:{hash_key}"
