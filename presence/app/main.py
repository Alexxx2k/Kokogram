from fastapi import FastAPI

app = FastAPI(title="presence")

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
