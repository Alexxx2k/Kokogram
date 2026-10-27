from fastapi import FastAPI

app = FastAPI(title="gateway")

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
