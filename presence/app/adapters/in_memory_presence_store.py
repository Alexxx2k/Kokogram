from datetime import datetime
from uuid import UUID

from kokogram_shared.clock import Clock


class InMemoryPresenceStore:
    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock
        self._connections: dict[str, tuple[UUID, datetime]] = {}
        self._user_connections: dict[UUID, set[str]] = {}
        self._expirations: dict[str, float] = {}
        self._conn_subscriptions: dict[str, set[UUID]] = {}
        self._user_subscribers: dict[UUID, set[str]] = {}

    def set_clock(self, clock: Clock) -> None:
        self._clock = clock

    def clear(self) -> None:
        self._connections.clear()
        self._user_connections.clear()
        self._expirations.clear()
        self._conn_subscriptions.clear()
        self._user_subscribers.clear()

    async def register_connection(
        self, connection_id: str, user_id: UUID, expires_at: datetime
    ) -> bool:
        old_data = self._connections.get(connection_id)
        if old_data is not None and old_data[0] != user_id:
            old_user_id = old_data[0]
            conns = self._user_connections.get(old_user_id)
            if conns is not None:
                conns.discard(connection_id)
                if not conns:
                    self._user_connections.pop(old_user_id, None)

        user_conns = self._user_connections.setdefault(user_id, set())
        is_first = len(user_conns) == 0

        self._connections[connection_id] = (user_id, expires_at)
        user_conns.add(connection_id)
        self._expirations[connection_id] = expires_at.timestamp()

        return is_first

    async def remove_connection(self, connection_id: str) -> tuple[UUID | None, bool]:
        conn_data = self._connections.pop(connection_id, None)
        self._expirations.pop(connection_id, None)

        subscribed_users = self._conn_subscriptions.pop(connection_id, set())
        for target_id in subscribed_users:
            subs = self._user_subscribers.get(target_id)
            if subs:
                subs.discard(connection_id)
                if not subs:
                    self._user_subscribers.pop(target_id, None)

        if conn_data is None:
            return None, False

        user_id, _ = conn_data
        user_conns = self._user_connections.get(user_id)
        is_last = False
        if user_conns is not None:
            user_conns.discard(connection_id)
            if len(user_conns) == 0:
                is_last = True
                self._user_connections.pop(user_id, None)

        return user_id, is_last

    async def ping_connection(self, connection_id: str, expires_at: datetime) -> bool:
        conn_data = self._connections.get(connection_id)
        if conn_data is None:
            return False

        if self._clock is not None:
            now_ts = self._clock.now().timestamp()
            if self._expirations.get(connection_id, 0.0) <= now_ts:
                await self.remove_connection(connection_id)
                return False

        user_id, _ = conn_data
        self._connections[connection_id] = (user_id, expires_at)
        self._expirations[connection_id] = expires_at.timestamp()
        return True

    async def get_expired_connections(self, now: datetime) -> list[str]:
        now_ts = now.timestamp()
        return [conn_id for conn_id, expire_ts in self._expirations.items() if expire_ts <= now_ts]

    async def add_subscriptions(self, connection_id: str, target_user_ids: list[UUID]) -> None:
        if not target_user_ids:
            return
        conn_subs = self._conn_subscriptions.setdefault(connection_id, set())
        for user_id in target_user_ids:
            conn_subs.add(user_id)
            user_subs = self._user_subscribers.setdefault(user_id, set())
            user_subs.add(connection_id)

    async def remove_subscriptions(self, connection_id: str, target_user_ids: list[UUID]) -> None:
        if not target_user_ids:
            return
        conn_subs = self._conn_subscriptions.get(connection_id)
        for user_id in target_user_ids:
            if conn_subs:
                conn_subs.discard(user_id)
            user_subs = self._user_subscribers.get(user_id)
            if user_subs:
                user_subs.discard(connection_id)
                if not user_subs:
                    self._user_subscribers.pop(user_id, None)

    async def get_user_statuses(self, user_ids: list[UUID]) -> dict[UUID, bool]:
        now_ts = self._clock.now().timestamp() if self._clock is not None else None
        result: dict[UUID, bool] = {}
        for user_id in user_ids:
            conns = self._user_connections.get(user_id)
            if not conns:
                result[user_id] = False
                continue
            if now_ts is None:
                result[user_id] = len(conns) > 0
            else:
                has_alive = any(self._expirations.get(c_id, 0.0) > now_ts for c_id in conns)
                result[user_id] = has_alive
        return result

    async def get_subscribers_for_user(self, user_id: UUID) -> set[str]:
        subs = self._user_subscribers.get(user_id)
        if not subs:
            return set()
        return set(subs)
