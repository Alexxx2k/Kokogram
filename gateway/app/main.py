from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from kokogram_shared.fastapi_handlers import register_error_handlers
from kokogram_shared.fastapi_middleware import setup_observability

from gateway.app.api.dependencies import close_http_client, get_connection_registry
from gateway.app.api.internal import router as internal_router
from gateway.app.api.proxy import router as proxy_router
from gateway.app.api.ws import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    await get_connection_registry().close_all()
    await close_http_client()


app = FastAPI(title="gateway", lifespan=lifespan)
setup_observability(app, service="gateway")
register_error_handlers(app)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(ws_router)
app.include_router(internal_router)
app.include_router(proxy_router)
