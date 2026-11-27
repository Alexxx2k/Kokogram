from gateway.app.api.internal import router as internal_router
from gateway.app.api.proxy import router
from gateway.app.api.ws import router as ws_router

__all__ = ["internal_router", "router", "ws_router"]
