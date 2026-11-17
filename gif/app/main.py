import os
import sys

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))


from kokogram_shared.fastapi_handlers import register_error_handlers
from kokogram_shared.fastapi_middleware import setup_observability

from gif.app.config import settings
from gif.app.exceptions import GifUnavailableError
from gif.app.adapters.giphy_http import GiphyHttpClient
from gif.app.adapters.cdn_http import CdnHttpClient
from gif.app.adapters.cache_memory import MemoryGifCache
from gif.app.services.search import SearchService
from gif.app.services.check import CheckService

app = FastAPI(title="gif")
register_error_handlers(app)

giphy_client = GiphyHttpClient()
cdn_client = CdnHttpClient()
gif_cache = MemoryGifCache()

search_service = SearchService(giphy=giphy_client, cache=gif_cache)
check_service = CheckService(cdn=cdn_client, cache=gif_cache)


class GifDTO(BaseModel):
    send_url: str
    preview_url: str


class SearchResponse(BaseModel):
    gifs: list[GifDTO]


class CheckResponse(BaseModel):
    valid: bool
    reason: str | None = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/gifs/search", response_model=SearchResponse)
async def search(q: str = ""):
    if len(q) > 20:
        raise HTTPException(status_code=400, detail={"error": "validation_error", "message": "query_too_long"})
    gifs = await search_service.search(q)
    return {"gifs": gifs}


@app.get("/gifs/trending", response_model=SearchResponse)
async def trending():
    gifs = await search_service.trending()
    return {"gifs": gifs}


@app.get("/internal/gifs/check", response_model=CheckResponse)
async def check(url: str):
    return await check_service.check(url)


@app.exception_handler(GifUnavailableError)
async def gif_unavailable_handler(request: Request, exc: GifUnavailableError):
    return JSONResponse(status_code=503, content={"error": "gif_unavailable"})


setup_observability(app, service="gif")
