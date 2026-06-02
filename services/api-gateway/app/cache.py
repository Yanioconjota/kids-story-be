"""
Redis story cache for api-gateway.

Cache failures degrade gracefully — they never break the request flow.
"""

import hashlib
import json
import os
from typing import Optional

from shared.contracts.story import Story, StoryRequest

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
STORY_CACHE_TTL = int(os.getenv("STORY_CACHE_TTL", "3600"))  # 1 hour default

_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is None:
        import redis.asyncio as redis  # noqa: PLC0415
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


def build_story_cache_key(request: StoryRequest) -> str:
    """Deterministic key covering all inputs that affect the generated story."""
    raw = f"{request.child_theme}|{request.character_name}|{request.prompt or ''}|{request.max_words}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:24]
    return f"story:v1:{digest}"


async def get_cached_story(request: StoryRequest) -> Optional[Story]:
    try:
        key = build_story_cache_key(request)
        data = await _get_redis().get(key)
        if data:
            print(f"[api-gateway] Cache HIT: {key}")
            return Story(**json.loads(data))
        print(f"[api-gateway] Cache MISS: {key}")
        return None
    except Exception as exc:
        print(f"[api-gateway] Cache GET error (degraded): {exc}")
        return None


async def set_cached_story(request: StoryRequest, story: Story) -> None:
    try:
        key = build_story_cache_key(request)
        await _get_redis().setex(key, STORY_CACHE_TTL, story.model_dump_json())
    except Exception as exc:
        print(f"[api-gateway] Cache SET error (degraded): {exc}")


async def delete_cached_story(request: StoryRequest) -> bool:
    """Delete the cache entry for a specific story request. Returns True if a key was removed."""
    try:
        key = build_story_cache_key(request)
        deleted = await _get_redis().delete(key)
        return deleted > 0
    except Exception as exc:
        print(f"[api-gateway] Cache DELETE error (degraded): {exc}")
        return False


async def clear_all_story_cache() -> int:
    """Delete all story:v1:* keys. Returns the number of keys removed."""
    try:
        redis = _get_redis()
        keys = [key async for key in redis.scan_iter("story:v1:*")]
        if not keys:
            return 0
        return await redis.delete(*keys)
    except Exception as exc:
        print(f"[api-gateway] Cache CLEAR error (degraded): {exc}")
        return 0
