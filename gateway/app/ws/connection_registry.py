import asyncio
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
    def __init__(self, send_timeout: float = 1.5) -> None:
        self._connections: dict[str, WsConnection] = {}
        self._connection_users: dict[str, str] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._tasks: set[asyncio.Task[Any]] = set()
        self._send_timeout = send_timeout

    def register(
        self,
        connection_id: str,
        websocket: WsConnection,
        user_id: str | None = None,
    ) -> None:
        self._connections[connection_id] = websocket
        self._locks[connection_id] = asyncio.Lock()
        if user_id is not None:
            self._connection_users[connection_id] = str(user_id)

    def unregister(self, connection_id: str) -> None:
        self._connections.pop(connection_id, None)
        self._connection_users.pop(connection_id, None)
        self._locks.pop(connection_id, None)

    def track_task(self, task: asyncio.Task[Any]) -> None:
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

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
        lock = self._locks.get(connection_id)
        if ws is None or lock is None:
            return False

        async with lock:
            if self._connections.get(connection_id) is not ws:
                return False

            try:
                await asyncio.wait_for(ws.send_json(message), timeout=self._send_timeout)
                return True
            except TimeoutError:
                logger.warning(
                    "Таймаут отправки WS-сообщения в соединение %s (%.2f с)",
                    connection_id,
                    self._send_timeout,
                )
            except Exception as exc:
                logger.warning(
                    "Не удалось отправить WS-сообщение в соединение %s: %s",
                    connection_id,
                    exc,
                )

            if self._connections.get(connection_id) is ws:
                self.unregister(connection_id)
            return False

    async def _deliver_for_connection(
        self,
        connection_id: str,
        items: Sequence[WsDeliveryItem],
    ) -> int:
        delivered = 0
        for item in items:
            message = {"type": item.type, "payload": item.payload}
            if await self.send(connection_id, message):
                delivered += 1
            else:
                break
        return delivered

    async def deliver(self, deliveries: Sequence[WsDeliveryItem]) -> int:
        if not deliveries:
            return 0

        grouped: dict[str, list[WsDeliveryItem]] = {}
        for item in deliveries:
            grouped.setdefault(item.connection_id, []).append(item)

        if len(grouped) == 1:
            conn_id, items = next(iter(grouped.items()))
            return await self._deliver_for_connection(conn_id, items)

        results = await asyncio.gather(
            *(self._deliver_for_connection(conn_id, items) for conn_id, items in grouped.items())
        )
        return sum(results)

    async def close_all(self, code: int = 1001) -> None:
        items = list(self._connections.items())
        self._connections.clear()
        self._connection_users.clear()
        self._locks.clear()

        async def _close_one(connection_id: str, ws: WsConnection) -> None:
            try:
                await asyncio.wait_for(ws.close(code=code), timeout=self._send_timeout)
            except Exception as exc:
                logger.warning(
                    "Ошибка при закрытии WS-соединения %s: %s",
                    connection_id,
                    exc,
                )

        if items:
            await asyncio.gather(*(_close_one(conn_id, ws) for conn_id, ws in items))

    async def wait_tasks(self, timeout: float = 5.0) -> None:
        current = asyncio.current_task()
        pending = {task for task in self._tasks if task is not current and not task.done()}
        if not pending:
            return

        grace = min(timeout / 2, 2.0)
        _, still_pending = await asyncio.wait(pending, timeout=grace)
        if not still_pending:
            return

        for task in still_pending:
            task.cancel()

        remaining = max(timeout - grace, 0.5)
        await asyncio.wait(still_pending, timeout=remaining)
