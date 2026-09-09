import json
import logging
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self) -> None:
        self.client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )

    def ping(self) -> bool:
        try:
            return bool(self.client.ping())
        except RedisError:
            return False

    def get_json(self, key: str) -> Any | None:
        try:
            value = self.client.get(key)
            return json.loads(value) if value else None
        except (RedisError, json.JSONDecodeError) as exc:
            logger.warning("Redis read failed: %s", exc)
            return None

    def set_json(self, key: str, value: Any, ttl: int | None = None) -> None:
        try:
            self.client.setex(
                key,
                ttl or settings.cache_ttl_seconds,
                json.dumps(value, ensure_ascii=False, default=str),
            )
        except RedisError as exc:
            logger.warning("Redis write failed: %s", exc)

    def delete_pattern(self, pattern: str) -> None:
        try:
            keys = list(self.client.scan_iter(pattern, count=200))
            if keys:
                self.client.delete(*keys)
        except RedisError as exc:
            logger.warning("Redis invalidation failed: %s", exc)


cache = CacheService()
