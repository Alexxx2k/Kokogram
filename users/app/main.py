from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from kokogram_shared.fastapi_handlers import register_error_handlers
from kokogram_shared.fastapi_middleware import setup_observability

from app.adapters.database import Database
from app.api.auth import router as auth_router
from app.api.internal import router as internal_router
from app.config import Settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    database = Database(Settings.from_env().database_url)
    app.state.database = database
    try:
        yield
    finally:
        await database.close()


app = FastAPI(title="users", lifespan=lifespan)
setup_observability(app, service="users")
register_error_handlers(app)
app.include_router(auth_router)
app.include_router(internal_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
