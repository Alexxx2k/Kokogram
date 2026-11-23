import logging

from kokogram_shared import AppError

from gif.app.config import settings
from gif.app.ports.cache import GifCache
from gif.app.ports.cdn import CdnClient
from gif.app.services.url_validator import validate_url

logger = logging.getLogger("gif")


class CheckService:
    def __init__(self, cdn: CdnClient, cache: GifCache):
        self.cdn = cdn
        self.cache = cache

    async def check(self, url: str) -> dict:
        is_valid, reason = validate_url(url, settings.ALLOWED_HOSTS)
        if not is_valid:
            logger.warning("url_invalid", extra={"url": url, "reason": reason})
            return {"valid": False, "reason": reason}

        cache_key = f"check:{url}"
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info("cache_hit", extra={"key": cache_key})
            return {"valid": True, "reason": None}

        logger.info("cdn_request", extra={"url": url})
        try:
            content_length = await self.cdn.get_content_length(url)
        except AppError:
            logger.error("cdn_unavailable", extra={"url": url})
            raise

        if content_length is None:
            return {"valid": False, "reason": "size_unknown"}

        if content_length > 50 * 1024 * 1024:
            logger.warning("file_too_large", extra={"url": url, "size": content_length})
            return {"valid": False, "reason": "file_too_large"}

        await self.cache.set(cache_key, "valid", settings.CACHE_TTL_CHECK)
        return {"valid": True, "reason": None}
