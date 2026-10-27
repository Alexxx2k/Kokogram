from fastapi import FastAPI

app = FastAPI(title="gif")

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
