from gif.app.ports.cdn import CdnClient
from gif.app.ports.cache import GifCache
from gif.app.services.url_validator import validate_url
from gif.app.config import settings

class CheckService:
    def __init__(self, cdn: CdnClient, cache: GifCache):
        self.cdn = cdn
        self.cache = cache

    async def check(self, url: str) -> dict:
        is_valid, reason = validate_url(url, settings.ALLOWED_HOSTS)
        if not is_valid:
            return {"valid": False, "reason": reason}

        cache_key = f"check:{url}"
        cached = await self.cache.get(cache_key)
        if cached:
            return {"valid": True, "reason": None}

        content_length = await self.cdn.get_content_length(url)
        if content_length is None:
            return {"valid": False, "reason": "size_unknown"}
        if content_length > 50 * 1024 * 1024:
            return {"valid": False, "reason": "file_too_large"}

        await self.cache.set(cache_key, "valid", settings.CACHE_TTL_CHECK)
        return {"valid": True, "reason": None}
