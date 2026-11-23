from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from presence.app.api.dependencies import get_connection_service
from presence.app.api.schemas import (
    ConnectionCreateRequest,
    SubscriptionsResponse,
    SubscriptionUpdateRequest,
    UserStatusItem,
)
from presence.app.services.connection_service import ConnectionService

router = APIRouter(prefix="/internal/presence", tags=["presence"])


@router.post("/connections", status_code=status.HTTP_204_NO_CONTENT)
async def register_connection(
    payload: ConnectionCreateRequest,
    service: Annotated[ConnectionService, Depends(get_connection_service)],
) -> Response:
    await service.register_connection(
        connection_id=payload.connection_id,
        user_id=payload.user_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect(
    connection_id: str,
    service: Annotated[ConnectionService, Depends(get_connection_service)],
) -> Response:
    await service.disconnect(connection_id=connection_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/connections/{connection_id}/ping", status_code=status.HTTP_204_NO_CONTENT)
async def ping(
    connection_id: str,
    service: Annotated[ConnectionService, Depends(get_connection_service)],
) -> Response:
    await service.ping(connection_id=connection_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/connections/{connection_id}/subscriptions", response_model=SubscriptionsResponse)
async def update_subscriptions(
    connection_id: str,
    payload: SubscriptionUpdateRequest,
    service: Annotated[ConnectionService, Depends(get_connection_service)],
) -> SubscriptionsResponse:
    statuses_map = await service.update_subscriptions(
        connection_id=connection_id,
        add=payload.add,
        remove=payload.remove,
    )
    return SubscriptionsResponse(
        statuses=[
            UserStatusItem(user_id=user_id, online=online)
            for user_id, online in statuses_map.items()
        ]
    )
