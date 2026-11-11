from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from kokogram_shared.clock import Clock
from kokogram_shared.ids import IdGenerator, UuidGenerator
from kokogram_shared.logging import (
    configure_logging,
    reset_request_id,
    reset_user_id,
    set_request_id,
    set_user_id,
)

REQUEST_ID_HEADER = "X-Request-ID"
USER_ID_HEADER = "X-User-Id"


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, id_generator: IdGenerator | None = None) -> None:
        super().__init__(app)
        self._id_generator = id_generator or UuidGenerator()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(self._id_generator.new_id())
        user_id = request.headers.get(USER_ID_HEADER)

        request.state.request_id = request_id
        req_token = set_request_id(request_id)
        user_token = set_user_id(user_id)
        try:
            response = await call_next(request)
        finally:
            reset_user_id(user_token)
            reset_request_id(req_token)

        response.headers[REQUEST_ID_HEADER] = request_id
        return response


def setup_observability(
    app: FastAPI,
    service: str,
    id_generator: IdGenerator | None = None,
    clock: Clock | None = None,
) -> None:
    configure_logging(service=service, clock=clock)
    app.add_middleware(RequestContextMiddleware, id_generator=id_generator)
