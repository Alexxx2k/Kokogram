from typing import Annotated

import httpx
from fastapi import Depends
from kokogram_shared.clock import Clock, SystemClock
from redis.asyncio import Redis

from presence.app.adapters.http_gateway_client import HttpGatewayClient
from presence.app.adapters.in_memory_gateway_client import InMemoryGatewayClient
from presence.app.adapters.in_memory_presence_store import InMemoryPresenceStore
from presence.app.adapters.redis_presence_store import RedisPresenceStore
from presence.app.config import PresenceConfig
from presence.app.ports.gateway_client import GatewayClient
from presence.app.ports.presence_store import PresenceStore
from presence.app.services.connection_service import ConnectionService

_in_memory_store = InMemoryPresenceStore(clock=SystemClock())
_in_memory_gateway_client = InMemoryGatewayClient()
_redis_client: Redis | None = None
_http_client: httpx.AsyncClient | None = None


def get_presence_config() -> PresenceConfig:
    return PresenceConfig.from_env()


def get_clock() -> Clock:
    return SystemClock()


def get_redis_client(
    config: Annotated[PresenceConfig, Depends(get_presence_config)],
) -> Redis | None:
    global _redis_client
    if config.use_in_memory_store:
        return None
    if _redis_client is None:
        _redis_client = Redis.from_url(config.redis_url)
    return _redis_client


async def close_redis_client() -> None:
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
        finally:
            _redis_client = None


def get_presence_store(
    config: Annotated[PresenceConfig, Depends(get_presence_config)],
    redis: Annotated[Redis | None, Depends(get_redis_client)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> PresenceStore:
    if config.use_in_memory_store or redis is None:
        _in_memory_store.set_clock(clock)
        return _in_memory_store
    return RedisPresenceStore(redis, clock=clock)


def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
    return _http_client


async def close_http_client() -> None:
    global _http_client
    if _http_client is not None:
        try:
            if not _http_client.is_closed:
                await _http_client.aclose()
        finally:
            _http_client = None


def get_gateway_client(
    config: Annotated[PresenceConfig, Depends(get_presence_config)],
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> GatewayClient:
    if config.use_mock_gateway:
        return _in_memory_gateway_client
    return HttpGatewayClient(base_url=config.gateway_url, client=http_client)


def get_connection_service(
    store: Annotated[PresenceStore, Depends(get_presence_store)],
    gateway_client: Annotated[GatewayClient, Depends(get_gateway_client)],
    clock: Annotated[Clock, Depends(get_clock)],
    config: Annotated[PresenceConfig, Depends(get_presence_config)],
) -> ConnectionService:
    return ConnectionService(
        store=store,
        gateway_client=gateway_client,
        clock=clock,
        ttl_seconds=config.connection_ttl_seconds,
    )
