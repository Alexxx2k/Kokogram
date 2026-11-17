from fastapi import FastAPI
from kokogram_shared.fastapi_handlers import register_error_handlers
from kokogram_shared.fastapi_middleware import setup_observability

app = FastAPI(title="users")
setup_observability(app, service="users")
register_error_handlers(app)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
