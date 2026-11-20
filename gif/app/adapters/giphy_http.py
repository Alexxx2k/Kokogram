import httpx
from kokogram_shared import AppError, ErrorCode

from gif.app.config import settings


class GiphyHttpClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=settings.GIPHY_BASE_URL, timeout=settings.GIPHY_TIMEOUT
        )

    async def _get(self, path: str, params: dict) -> list[dict]:
        try:
            resp = await self.client.get(path, params=params)
            resp.raise_for_status()
            return resp.json().get("data", [])
        except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError):
            raise AppError(ErrorCode.GIF_UNAVAILABLE)

    async def search(self, q: str, limit: int) -> list[dict]:
        return await self._get("/v1/gifs/search", {"q": q, "limit": limit})

    async def trending(self, limit: int) -> list[dict]:
        return await self._get("/v1/gifs/trending", {"limit": limit})
