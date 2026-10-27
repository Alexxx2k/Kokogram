from fastapi import FastAPI

app = FastAPI(title="messages")

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
