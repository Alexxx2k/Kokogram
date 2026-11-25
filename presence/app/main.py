from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from kokogram_shared.fastapi_handlers import register_error_handlers
from kokogram_shared.fastapi_middleware import setup_observability

from presence.app.api.dependencies import (
    close_http_client,
    close_redis_client,
    get_clock,
    get_connection_service,
    get_gateway_client,
    get_http_client,
    get_presence_config,
    get_presence_store,
    get_redis_client,
)
from presence.app.api.router import router as presence_router
from presence.app.services.expiration_watcher import ExpirationWatcher


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    watcher: ExpirationWatcher | None = None
    config = get_presence_config()
    if config.enable_expiration_watcher:
        clock = get_clock()
        redis = get_redis_client(config)
        store = get_presence_store(config, redis, clock)
        http_client = get_http_client()
        gateway_client = get_gateway_client(config, http_client)
        service = get_connection_service(store, gateway_client, clock, config)
        watcher = ExpirationWatcher(
            connection_service=service,
            interval_seconds=config.expiration_check_interval_seconds,
        )
        watcher.start()

    yield

    if watcher is not None:
        await watcher.stop()

    await close_redis_client()
    await close_http_client()


app = FastAPI(title="presence", lifespan=lifespan)
setup_observability(app, service="presence")
register_error_handlers(app)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(presence_router)
