import time


class MemoryGifCache:
    def __init__(self):
        self._cache: dict[str, tuple[str, float]] = {}

    async def get(self, key: str) -> str | None:
        if key in self._cache:
            val, expire_at = self._cache[key]
            if time.time() < expire_at:
                return val
            del self._cache[key]
        return None

    async def set(self, key: str, value: str, ttl: int) -> None:
        self._cache[key] = (value, time.time() + ttl)
