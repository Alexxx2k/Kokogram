import httpx
from kokogram_shared import AppError, ErrorCode


class CdnHttpClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=1.0)

    async def get_content_length(self, url: str) -> int | None:
        try:
            resp = await self.client.head(url, follow_redirects=False)
            resp.raise_for_status()
            length = resp.headers.get("Content-Length")
            return int(length) if length else None
        except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError):
            raise AppError(ErrorCode.GIF_UNAVAILABLE)
