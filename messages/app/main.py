from fastapi import FastAPI
from kokogram_shared.fastapi_handlers import register_error_handlers

app = FastAPI(title="messages")
register_error_handlers(app)

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
