from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from kokogram_shared.fastapi_handlers import register_error_handlers
from kokogram_shared.fastapi_middleware import setup_observability

from app.adapters.avatar_storage import S3AvatarStorage
from app.adapters.database import Database
from app.api.auth import router as auth_router
from app.api.avatars import router as avatars_router
from app.api.internal import router as internal_router
from app.api.users import router as users_router
from app.config import Settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings.from_env()
    if not settings.url_signing_secret:
        raise ValueError("Задайте URL_SIGNING_SECRET для подписанных ссылок")
    database = Database(settings.database_url)
    app.state.database = database
    try:
        storage = S3AvatarStorage(settings)
        app.state.avatar_storage = storage
        try:
            yield
        finally:
            await storage.close()
    finally:
        await database.close()


app = FastAPI(title="users", lifespan=lifespan)
setup_observability(app, service="users")
register_error_handlers(app)
app.include_router(auth_router)
app.include_router(internal_router)
app.include_router(users_router)
app.include_router(avatars_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
