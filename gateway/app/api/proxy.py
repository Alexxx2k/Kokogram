from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from kokogram_shared.errors import AppError, ErrorCode
from kokogram_shared.logging import get_request_id, set_user_id

from gateway.app.api.dependencies import (
    get_gateway_config,
    get_http_client,
    get_route_table,
    get_users_client,
)
from gateway.app.config import GatewayConfig
from gateway.app.ports.users_client import UsersClient
from gateway.app.routing.route_table import RouteTable

router = APIRouter()

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
}

EXCLUDED_RESPONSE_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-length",
    "content-encoding",
}


async def forward_stream(
    request: Request,
    target_url: str,
    client: httpx.AsyncClient,
    user_id: str | None = None,
) -> StreamingResponse:
    headers: dict[str, str] = {}
    for k, v in request.headers.items():
        lower_k = k.lower()
        if lower_k in HOP_BY_HOP_HEADERS or lower_k == "x-user-id":
            continue
        headers[k] = v

    if user_id is not None:
        headers["X-User-Id"] = str(user_id)

    req_id = getattr(request.state, "request_id", None) or get_request_id()
    if req_id:
        headers["X-Request-ID"] = req_id

    content = None
    if request.method not in ("GET", "HEAD", "OPTIONS") or (
        "content-length" in request.headers or "transfer-encoding" in request.headers
    ):
        content = request.stream()

    try:
        upstream_req = client.build_request(
            method=request.method,
            url=target_url,
            content=content,
            headers=headers,
        )
        upstream_resp = await client.send(upstream_req, stream=True)
    except httpx.RequestError as exc:
        raise AppError(ErrorCode.SERVICE_UNAVAILABLE) from exc

    async def body_stream():
        try:
            async for chunk in upstream_resp.aiter_bytes():
                yield chunk
        except httpx.RequestError:
            return
        finally:
            await upstream_resp.aclose()

    resp_headers = {
        k: v for k, v in upstream_resp.headers.items() if k.lower() not in EXCLUDED_RESPONSE_HEADERS
    }

    return StreamingResponse(
        body_stream(),
        status_code=upstream_resp.status_code,
        headers=resp_headers,
        media_type=upstream_resp.headers.get("content-type"),
    )


@router.api_route(
    "/internal/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def reject_internal_direct(path: str) -> None:
    raise AppError(ErrorCode.NOT_FOUND)


@router.api_route(
    "/internal",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def reject_internal_root() -> None:
    raise AppError(ErrorCode.NOT_FOUND)


@router.api_route(
    "/api/v1/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_api_v1(
    path: str,
    request: Request,
    route_table: Annotated[RouteTable, Depends(get_route_table)],
    config: Annotated[GatewayConfig, Depends(get_gateway_config)],
    users_client: Annotated[UsersClient, Depends(get_users_client)],
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> StreamingResponse:
    full_path = request.url.path

    if route_table.is_internal(full_path):
        raise AppError(ErrorCode.NOT_FOUND)

    target_service = route_table.match_service(full_path)
    if target_service is None:
        raise AppError(ErrorCode.NOT_FOUND)

    user_id: str | None = None
    if route_table.is_public_endpoint(request.method, full_path):
        user_id = None
    elif route_table.is_signed_url(request.method, full_path, request.query_params):
        user_id = None
    else:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise AppError(ErrorCode.UNAUTHORIZED)

        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or parts[0] != "Bearer":
            raise AppError(ErrorCode.UNAUTHORIZED)

        token = parts[1].strip()
        if not token:
            raise AppError(ErrorCode.UNAUTHORIZED)

        user_id = await users_client.verify_session(token)
        if not user_id:
            raise AppError(ErrorCode.UNAUTHORIZED)

        set_user_id(str(user_id))

    base_url = config.get_service_url(target_service).rstrip("/")
    target_path = route_table.strip_api_prefix(full_path)
    target_url = f"{base_url}{target_path}"
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    return await forward_stream(
        request=request,
        target_url=target_url,
        client=http_client,
        user_id=user_id,
    )
