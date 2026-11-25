import logging
from datetime import timedelta
from uuid import UUID

from kokogram_shared.clock import Clock
from kokogram_shared.errors import AppError, ErrorCode

from presence.app.ports.gateway_client import GatewayClient, WsDelivery
from presence.app.ports.presence_store import PresenceStore

logger = logging.getLogger(__name__)


class ConnectionService:
    def __init__(
        self,
        store: PresenceStore,
        gateway_client: GatewayClient,
        clock: Clock,
        ttl_seconds: int = 75,
    ) -> None:
        self._store = store
        self._gateway_client = gateway_client
        self._clock = clock
        self._ttl_seconds = ttl_seconds

    async def register_connection(self, connection_id: str, user_id: UUID) -> None:
        expires_at = self._clock.now() + timedelta(seconds=self._ttl_seconds)
        is_first = await self._store.register_connection(connection_id, user_id, expires_at)

        if is_first:
            await self._notify_subscribers(user_id=user_id, online=True)

    async def disconnect(self, connection_id: str) -> None:
        user_id, is_last = await self._store.remove_connection(connection_id)
        if user_id is not None and is_last:
            await self._notify_subscribers(user_id=user_id, online=False)

    async def ping(self, connection_id: str) -> None:
        expires_at = self._clock.now() + timedelta(seconds=self._ttl_seconds)
        found = await self._store.ping_connection(connection_id, expires_at)
        if not found:
            raise AppError(ErrorCode.NOT_FOUND, "Соединение не найдено")

    async def update_subscriptions(
        self, connection_id: str, add: list[UUID], remove: list[UUID]
    ) -> dict[UUID, bool]:
        if not await self._store.connection_exists(connection_id):
            raise AppError(ErrorCode.NOT_FOUND, "Соединение не найдено")

        if remove:
            await self._store.remove_subscriptions(connection_id, remove)

        if not add:
            return {}

        await self._store.add_subscriptions(connection_id, add)
        return await self._store.get_user_statuses(add)

    async def run_once(self) -> list[str]:
        now = self._clock.now()
        expired_conn_ids = await self._store.get_expired_connections(now)
        for conn_id in expired_conn_ids:
            user_id, is_last = await self._store.remove_connection(conn_id)
            if user_id is not None and is_last:
                await self._notify_subscribers(user_id=user_id, online=False)
        return expired_conn_ids

    async def _notify_subscribers(self, user_id: UUID, online: bool) -> None:
        try:
            subscribers = await self._store.get_subscribers_for_user(user_id)
            if not subscribers:
                return

            deliveries = [
                WsDelivery(
                    connection_id=sub_conn_id,
                    type="status_changed",
                    payload={"user_id": str(user_id), "online": online},
                )
                for sub_conn_id in subscribers
            ]
            await self._gateway_client.deliver(deliveries)
        except Exception as exc:
            error_code = str(exc.code) if isinstance(exc, AppError) else None
            logger.warning(
                "Не удалось отправить status_changed для %s (online=%s): %s",
                user_id,
                online,
                exc,
                extra={"user_id": str(user_id), "error_code": error_code},
            )
