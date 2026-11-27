import json
import logging

from kokogram_shared import AppError, ValidationReason

from gif.app.config import settings
from gif.app.ports.cache import GifCache
from gif.app.ports.giphy import GiphyClient
from gif.app.services.selector import GifVariant, GifVariantSelector

logger = logging.getLogger("gif")


class SearchService:
    def __init__(self, giphy: GiphyClient, cache: GifCache):
        self.giphy = giphy
        self.cache = cache
        self.selector = GifVariantSelector()

    def _map_giphy_response(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            images = item.get("images", {})
            gif_id = item.get("id")

            variants = []
            for variant_name, variant_data in images.items():
                try:
                    url = variant_data.get("url")
                    size_str = variant_data.get("size")
                    if url and size_str:
                        variants.append(GifVariant(url=url, size=int(size_str)))
                except (ValueError, TypeError):
                    continue

            selected = self.selector.select(variants)
            if selected and gif_id:
                result.append(
                    {"id": gif_id, "url": selected.send_url, "preview_url": selected.preview_url}
                )
        return result

    async def _get_gifs(self, q: str | None, limit: int) -> list[dict]:
        norm_q = (q or "").strip().lower()
        cache_key = f"search:{norm_q}:{limit}"

        cached = await self.cache.get(cache_key)
        if cached:
            logger.info("cache_hit", extra={"key": cache_key})
            return json.loads(cached)

        logger.info("cache_miss", extra={"key": cache_key})

        try:
            logger.info("giphy_request", extra={"q": norm_q, "limit": limit})
            if norm_q:
                raw_data = await self.giphy.search(norm_q, limit)
            else:
                raw_data = await self.giphy.trending(limit)
        except AppError:
            logger.error("giphy_unavailable", extra={"q": norm_q})
            raise

        result = self._map_giphy_response(raw_data)

        await self.cache.set(cache_key, json.dumps(result), settings.CACHE_TTL_SEARCH)
        for gif in result:
            await self.cache.set(f"check:{gif['url']}", "valid", settings.CACHE_TTL_CHECK)
        return result

    async def search(self, q: str) -> list[dict]:
        if len(q) > 20:
            raise AppError.validation(ValidationReason.QUERY_TOO_LONG, field="q")
        return await self._get_gifs(q, settings.DEFAULT_LIMIT)

    async def trending(self) -> list[dict]:
        return await self._get_gifs("", settings.DEFAULT_LIMIT)
