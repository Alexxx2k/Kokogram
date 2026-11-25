from kokogram_shared.errors import AppError, ErrorCode

from gateway.app.ports.presence_client import PresenceClient, UserStatus


class InMemoryPresenceClient(PresenceClient):
    def __init__(self) -> None:
        self._connections: dict[str, str] = {}
        self._user_connections: dict[str, set[str]] = {}
        self._subscriptions: dict[str, set[str]] = {}
        self._ping_counts: dict[str, int] = {}

    async def register_connection(self, connection_id: str, user_id: str) -> None:
        uid = str(user_id)
        self._connections[connection_id] = uid
        self._user_connections.setdefault(uid, set()).add(connection_id)
        self._subscriptions.setdefault(connection_id, set())
        self._ping_counts.setdefault(connection_id, 0)

    async def disconnect(self, connection_id: str) -> None:
        uid = self._connections.pop(connection_id, None)
        self._subscriptions.pop(connection_id, None)
        self._ping_counts.pop(connection_id, None)
        if uid is not None:
            conns = self._user_connections.get(uid)
            if conns is not None:
                conns.discard(connection_id)
                if not conns:
                    self._user_connections.pop(uid, None)

    async def ping(self, connection_id: str) -> None:
        if connection_id not in self._connections:
            raise AppError(ErrorCode.NOT_FOUND, "Соединение не найдено")
        self._ping_counts[connection_id] = self._ping_counts.get(connection_id, 0) + 1

    async def update_subscriptions(
        self,
        connection_id: str,
        add: list[str] | None = None,
        remove: list[str] | None = None,
    ) -> list[UserStatus]:
        if connection_id not in self._connections:
            raise AppError(ErrorCode.NOT_FOUND, "Соединение не найдено")

        subs = self._subscriptions.setdefault(connection_id, set())
        for uid in remove or []:
            subs.discard(str(uid))

        added = [str(uid) for uid in (add or [])]
        for uid in added:
            subs.add(uid)

        return [UserStatus(user_id=uid, online=self.is_online(uid)) for uid in added]

    def is_online(self, user_id: str) -> bool:
        return bool(self._user_connections.get(str(user_id)))

    def get_subscriptions(self, connection_id: str) -> set[str]:
        return set(self._subscriptions.get(connection_id, set()))

    def get_ping_count(self, connection_id: str) -> int:
        return self._ping_counts.get(connection_id, 0)

    def clear(self) -> None:
        self._connections.clear()
        self._user_connections.clear()
        self._subscriptions.clear()
        self._ping_counts.clear()
