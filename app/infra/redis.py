import json
from typing import Any

import redis

from app.infra.settings import Settings


def make_redis_client(settings: Settings) -> redis.Redis:
    return redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        decode_responses=True,
    )


class RedisStateStore:
    def __init__(self, client: redis.Redis, ttl_seconds: int) -> None:
        self.client = client
        self.ttl_seconds = ttl_seconds

    def set_json(self, key: str, value: dict[str, Any]) -> None:
        self.client.set(key, json.dumps(value), ex=self.ttl_seconds)

    def get_json(self, key: str) -> dict[str, Any] | None:
        raw = self.client.get(key)
        if raw is None:
            return None
        return dict(json.loads(raw))

    def delete(self, key: str) -> None:
        self.client.delete(key)