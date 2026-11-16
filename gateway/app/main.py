from fastapi import FastAPI
from kokogram_shared.fastapi_handlers import register_error_handlers
from kokogram_shared.fastapi_middleware import setup_observability

from gateway.app.api.proxy import router as proxy_router

app = FastAPI(title="gateway")
setup_observability(app, service="gateway")
register_error_handlers(app)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(proxy_router)
