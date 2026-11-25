from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class WsDelivery:
    connection_id: str
    type: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "connection_id": self.connection_id,
            "type": self.type,
            "payload": self.payload,
        }


class GatewayClient(Protocol):
    async def deliver(self, deliveries: list[WsDelivery]) -> None: ...
