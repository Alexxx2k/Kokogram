import logging

from fastapi import FastAPI
from kokogram_shared.fastapi_handlers import register_error_handlers
from kokogram_shared.fastapi_middleware import setup_observability
from pydantic import BaseModel

from gif.app.adapters.cache_redis import RedisGifCache
from gif.app.adapters.cdn_http import CdnHttpClient
from gif.app.adapters.giphy_http import GiphyHttpClient
from gif.app.config import settings
from gif.app.services.check import CheckService
from gif.app.services.search import SearchService

app = FastAPI(title="gif")
logger = logging.getLogger("gif")
register_error_handlers(app)

giphy_client = GiphyHttpClient()
cdn_client = CdnHttpClient()
gif_cache = RedisGifCache(settings.REDIS_URL)

search_service = SearchService(giphy=giphy_client, cache=gif_cache)
check_service = CheckService(cdn=cdn_client, cache=gif_cache)
setup_observability(app, service="gif")


class GifDTO(BaseModel):
    id: str
    url: str
    preview_url: str


class GifListResponse(BaseModel):
    items: list[GifDTO]


class CheckResponse(BaseModel):
    valid: bool
    reason: str | None = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/gifs/search", response_model=GifListResponse)
async def search(q: str = ""):
    items = await search_service.search(q)
    return {"items": items}


@app.get("/gifs/trending", response_model=GifListResponse)
async def trending():
    items = await search_service.trending()
    return {"items": items}


@app.get("/internal/gifs/check", response_model=CheckResponse)
async def check(url: str):
    return await check_service.check(url)
