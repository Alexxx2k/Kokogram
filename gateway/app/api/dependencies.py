import os
from typing import Annotated

import httpx
from fastapi import Depends
from kokogram_shared.ids import IdGenerator, UuidGenerator

from gateway.app.adapters.http_presence_client import HttpPresenceClient
from gateway.app.adapters.http_users_client import HttpUsersClient
from gateway.app.adapters.in_memory_presence_client import InMemoryPresenceClient
from gateway.app.adapters.in_memory_users_client import InMemoryUsersClient
from gateway.app.config import GatewayConfig
from gateway.app.ports.presence_client import PresenceClient
from gateway.app.ports.users_client import UsersClient
from gateway.app.routing.route_table import RouteTable
from gateway.app.ws.connection_registry import ConnectionRegistry
from gateway.app.ws.session_handler import WsSessionHandler

_route_table = RouteTable()
_http_client: httpx.AsyncClient | None = None
_in_memory_users_client = InMemoryUsersClient()
_in_memory_presence_client = InMemoryPresenceClient()
_connection_registry = ConnectionRegistry()
_id_generator = UuidGenerator()


def get_route_table() -> RouteTable:
    return _route_table


def get_gateway_config() -> GatewayConfig:
    return GatewayConfig.from_env()


def get_id_generator() -> IdGenerator:
    return _id_generator


def get_connection_registry() -> ConnectionRegistry:
    return _connection_registry


def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=5.0))
    return _http_client


async def close_http_client() -> None:
    global _http_client
    if _http_client is not None:
        try:
            if not _http_client.is_closed:
                await _http_client.aclose()
        finally:
            _http_client = None


def get_users_client(
    config: Annotated[GatewayConfig, Depends(get_gateway_config)],
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> UsersClient:
    use_mock = (
        os.getenv("USE_MOCK_USERS_CLIENT", "false").lower() in ("true", "1")
        or config.users_service_url == "mock"
    )
    if use_mock:
        return _in_memory_users_client
    return HttpUsersClient(base_url=config.users_service_url, client=http_client)


def get_presence_client(
    config: Annotated[GatewayConfig, Depends(get_gateway_config)],
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> PresenceClient:
    use_mock = (
        os.getenv("USE_MOCK_PRESENCE_CLIENT", "false").lower() in ("true", "1")
        or config.presence_service_url == "mock"
    )
    if use_mock:
        return _in_memory_presence_client
    return HttpPresenceClient(base_url=config.presence_service_url, client=http_client)


def get_ws_session_handler(
    presence_client: Annotated[PresenceClient, Depends(get_presence_client)],
) -> WsSessionHandler:
    return WsSessionHandler(presence_client=presence_client)
