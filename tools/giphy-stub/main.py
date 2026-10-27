import os

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

MB = 1024 * 1024
BASE = os.environ.get("PUBLIC_BASE_URL", "http://giphy-stub:8080")

# минимальный валидный GIF для GET-запросов к маленьким файлам
TINY_GIF = bytes.fromhex(
    "47494638396101000100800000000000ffffff21f90401000000002c00000000010001000002024401003b"
)

# размеры вариантов в байтах: подобраны под границы 1 МБ и 50 МБ (из NF_Gif_2 и NF_Gif_3)
ITEMS = {
    "small": {
        "title": "cat small",
        "variants": {"original": 2 * MB, "fixed_height": 600_000, "fixed_height_small": 200_000},
    },
    "boundary": {
        "title": "cat boundary",
        "variants": {"original": 50 * MB, "fixed_height": 5 * MB, "fixed_height_small": MB},
    },
    "too_big": {
        "title": "cat too big",
        "variants": {"original": 50 * MB + 1, "fixed_height": 50 * MB + 1, "fixed_height_small": 50 * MB + 1},
    },
    "no_preview": {
        "title": "cat no preview",
        "variants": {"original": 10 * MB, "fixed_height": 5 * MB, "fixed_height_small": MB + 1},
    },
}

app = FastAPI(title="giphy-stub")
state = {"fail": False}


def _gif(gif_id: str) -> dict:
    item = ITEMS[gif_id]
    images = {
        name: {"url": f"{BASE}/cdn/{gif_id}/{name}.gif", "size": str(size)}
        for name, size in item["variants"].items()
    }
    return {"id": gif_id, "title": item["title"], "images": images}


def _unavailable():
    return JSONResponse({"error": "stub failure mode"}, status_code=503)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/__admin/fail")
def set_failure(enabled: bool = True):
    state["fail"] = enabled
    return {"fail": enabled}


@app.get("/v1/gifs/search")
def search(q: str = "", limit: int = 25):
    if state["fail"]:
        return _unavailable()
    found = [_gif(i) for i, item in ITEMS.items() if q.lower() in item["title"]]
    return {"data": found[:limit], "meta": {"status": 200}}


@app.get("/v1/gifs/trending")
def trending(limit: int = 25):
    if state["fail"]:
        return _unavailable()
    return {"data": [_gif(i) for i in ITEMS][:limit], "meta": {"status": 200}}


@app.head("/cdn/{gif_id}/{variant}.gif")
def cdn_head(gif_id: str, variant: str):
    if state["fail"]:
        return Response(status_code=503)
    item = ITEMS.get(gif_id)
    if item is None or variant not in item["variants"]:
        return Response(status_code=404)
    return Response(
        status_code=200,
        media_type="image/gif",
        headers={"Content-Length": str(item["variants"][variant])},
    )


@app.get("/cdn/{gif_id}/{variant}.gif")
def cdn_get(gif_id: str, variant: str):
    if state["fail"]:
        return Response(status_code=503)
    item = ITEMS.get(gif_id)
    if item is None or variant not in item["variants"]:
        return Response(status_code=404)
    return Response(content=TINY_GIF, media_type="image/gif")
