import redis.asyncio as redis


class RedisGifCache:
    def __init__(self, redis_url: str):
        self.client = redis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> str | None:
        return await self.client.get(key)

    async def set(self, key: str, value: str, ttl: int) -> None:
        await self.client.set(key, value, ex=ttl)
