from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from kokogram_shared.errors import (
    DEFAULT_MESSAGE,
    HTTP_STATUS,
    AppError,
    ErrorCode,
    error_body,
)

_LOC_PREFIXES = {"body", "query", "path", "header", "cookie"}


async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.to_body())


async def _request_validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {
            "field": ".".join(str(p) for p in err["loc"] if p not in _LOC_PREFIXES) or None,
            "reason": err["type"],
        }
        for err in exc.errors()
    ]
    code = ErrorCode.VALIDATION_ERROR
    return JSONResponse(
        status_code=HTTP_STATUS[code],
        content=error_body(code, DEFAULT_MESSAGE[code], details),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _request_validation_handler)
