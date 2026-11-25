import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class WsConnection(Protocol):
    async def send_json(self, data: Any) -> None: ...

    async def close(self, code: int = 1000) -> None: ...


@dataclass(frozen=True)
class WsDeliveryItem:
    connection_id: str
    type: str
    payload: dict[str, Any]


class ConnectionRegistry:
    def __init__(self) -> None:
        self._connections: dict[str, WsConnection] = {}
        self._connection_users: dict[str, str] = {}

    def register(
        self,
        connection_id: str,
        websocket: WsConnection,
        user_id: str | None = None,
    ) -> None:
        self._connections[connection_id] = websocket
        if user_id is not None:
            self._connection_users[connection_id] = str(user_id)

    def unregister(self, connection_id: str) -> None:
        self._connections.pop(connection_id, None)
        self._connection_users.pop(connection_id, None)

    def get(self, connection_id: str) -> WsConnection | None:
        return self._connections.get(connection_id)

    def contains(self, connection_id: str) -> bool:
        return connection_id in self._connections

    def get_user_connections(self, user_id: str) -> list[str]:
        uid = str(user_id)
        return [conn_id for conn_id, owner in self._connection_users.items() if owner == uid]

    def __contains__(self, connection_id: str) -> bool:
        return connection_id in self._connections

    def __len__(self) -> int:
        return len(self._connections)

    async def send(self, connection_id: str, message: dict[str, Any]) -> bool:
        ws = self._connections.get(connection_id)
        if ws is None:
            return False

        try:
            await ws.send_json(message)
            return True
        except Exception as exc:
            logger.warning(
                "Не удалось отправить WS-сообщение в соединение %s: %s",
                connection_id,
                exc,
            )
            if self._connections.get(connection_id) is ws:
                self.unregister(connection_id)
            return False

    async def deliver(self, deliveries: Sequence[WsDeliveryItem]) -> int:
        delivered = 0
        for item in deliveries:
            message = {"type": item.type, "payload": item.payload}
            if await self.send(item.connection_id, message):
                delivered += 1
        return delivered

    async def close_all(self, code: int = 1001) -> None:
        items = list(self._connections.items())
        self._connections.clear()
        self._connection_users.clear()
        for connection_id, ws in items:
            try:
                await ws.close(code=code)
            except Exception as exc:
                logger.warning(
                    "Ошибка при закрытии WS-соединения %s: %s",
                    connection_id,
                    exc,
                )
