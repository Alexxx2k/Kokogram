from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, Field

from gateway.app.api.dependencies import get_connection_registry
from gateway.app.ws.connection_registry import ConnectionRegistry, WsDeliveryItem

router = APIRouter(prefix="/internal", tags=["internal"])


class WsDeliveryPayload(BaseModel):
    connection_id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class WsDeliverRequest(BaseModel):
    deliveries: list[WsDeliveryPayload] = Field(default_factory=list)


@router.post("/ws/deliver", status_code=status.HTTP_204_NO_CONTENT)
async def deliver_ws_messages(
    body: WsDeliverRequest,
    registry: Annotated[ConnectionRegistry, Depends(get_connection_registry)],
) -> Response:
    items = [
        WsDeliveryItem(
            connection_id=item.connection_id,
            type=item.type,
            payload=item.payload,
        )
        for item in body.deliveries
    ]
    await registry.deliver(items)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
