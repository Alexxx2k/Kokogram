from fastapi import FastAPI

app = FastAPI(title="chats")

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
