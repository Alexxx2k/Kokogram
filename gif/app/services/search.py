import json
import logging
from gif.app.ports.giphy import GiphyClient
from gif.app.ports.cache import GifCache
from gif.app.services.selector import GifVariantSelector, GifVariant
from gif.app.config import settings

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
            if selected:
                result.append({
                    "send_url": selected.send_url,
                    "preview_url": selected.preview_url
                })
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
            if norm_q:
                raw_data = await self.giphy.search(norm_q, limit)
            else:
                raw_data = await self.giphy.trending(limit)
            logger.info("giphy_request", extra={"q": norm_q, "limit": limit})
        except Exception as e:
            logger.error("giphy_unavailable", extra={"error": str(e)})
            raise

        result = self._map_giphy_response(raw_data)

        await self.cache.set(cache_key, json.dumps(result), settings.CACHE_TTL_SEARCH)
        return result

    async def search(self, q: str) -> list[dict]:
        if len(q) > 20:
            raise ValueError("query_too_long")
        return await self._get_gifs(q, settings.DEFAULT_LIMIT)

    async def trending(self) -> list[dict]:
        return await self._get_gifs("", settings.DEFAULT_LIMIT)
