from fastapi import FastAPI
from kokogram_shared.fastapi_handlers import register_error_handlers
from kokogram_shared.fastapi_middleware import setup_observability

from messages.app.api.routes import router

app = FastAPI(title="messages")
register_error_handlers(app)
setup_observability(app, service="messages")

app.include_router(router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
