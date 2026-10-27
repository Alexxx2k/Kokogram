from fastapi import FastAPI

app = FastAPI(title="users")

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
