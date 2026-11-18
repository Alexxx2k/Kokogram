import httpx

from gif.app.exceptions import GifUnavailableError


class CdnHttpClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=1.0)

    async def get_content_length(self, url: str) -> int | None:
        try:
            resp = await self.client.head(url, follow_redirects=False)
            resp.raise_for_status()
            length = resp.headers.get("Content-Length")
            return int(length) if length else None
        except (httpx.TimeoutException, httpx.HTTPStatusError):
            raise GifUnavailableError()
