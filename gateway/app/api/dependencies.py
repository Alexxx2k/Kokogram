import os
from typing import Annotated

import httpx
from fastapi import Depends

from gateway.app.adapters.http_users_client import HttpUsersClient
from gateway.app.adapters.in_memory_users_client import InMemoryUsersClient
from gateway.app.config import GatewayConfig
from gateway.app.ports.users_client import UsersClient
from gateway.app.routing.route_table import RouteTable

_route_table = RouteTable()
_http_client: httpx.AsyncClient | None = None


def get_route_table() -> RouteTable:
    return _route_table


def get_gateway_config() -> GatewayConfig:
    return GatewayConfig.from_env()


def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=5.0))
    return _http_client


def get_users_client(
    config: Annotated[GatewayConfig, Depends(get_gateway_config)],
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> UsersClient:
    use_mock = (
        os.getenv("USE_MOCK_USERS_CLIENT", "false").lower() in ("true", "1")
        or config.users_service_url == "mock"
    )
    if use_mock:
        return InMemoryUsersClient()
    return HttpUsersClient(base_url=config.users_service_url, client=http_client)
