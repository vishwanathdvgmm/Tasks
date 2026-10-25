import json
import time
from redis.asyncio import Redis
from app.config import settings

class RedisSessionStore:
    def __init__(self, redis: Redis):
        self.redis = redis

    @staticmethod
    def _key(session_id: str, suffix: str) -> str:
        return f"task08:session:{session_id}:{suffix}"

    async def load_messages(self, session_id: str) -> list[dict]:
        values = await self.redis.lrange(self._key(session_id, "messages"), 0, -1)
        result = []
        for value in values:
            try:
                result.append(json.loads(value))
            except (TypeError, json.JSONDecodeError):
                continue
        return result

    async def load_summary(self, session_id: str) -> str:
        return await self.redis.get(self._key(session_id, "summary")) or ""

    async def load_entities(self, session_id: str) -> dict:
        raw = await self.redis.get(self._key(session_id, "entities"))
        try:
            return json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return {}

    async def save_turn(self, session_id: str, user_message: str, assistant_message: str,
                        summary: str | None = None, entities: dict | None = None) -> None:
        now = time.time()
        messages_key = self._key(session_id, "messages")
        pipe = self.redis.pipeline(transaction=True)
        pipe.rpush(messages_key,
                   json.dumps({"role": "user", "content": user_message, "timestamp": now}),
                   json.dumps({"role": "assistant", "content": assistant_message, "timestamp": now}))
        pipe.expire(messages_key, settings.session_ttl_seconds)
        if summary is not None:
            summary_key = self._key(session_id, "summary")
            pipe.set(summary_key, summary, ex=settings.session_ttl_seconds)
        if entities is not None:
            entities_key = self._key(session_id, "entities")
            pipe.set(entities_key, json.dumps(entities), ex=settings.session_ttl_seconds)
        await pipe.execute()

    async def delete_session(self, session_id: str) -> int:
        keys = [self._key(session_id, suffix) for suffix in ("messages", "summary", "entities")]
        return await self.redis.delete(*keys)

    async def refresh_ttl(self, session_id: str) -> None:
        pipe = self.redis.pipeline(transaction=True)
        for suffix in ("messages", "summary", "entities"):
            pipe.expire(self._key(session_id, suffix), settings.session_ttl_seconds)
        await pipe.execute()
