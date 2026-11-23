import asyncio
import logging

from presence.app.services.connection_service import ConnectionService

logger = logging.getLogger(__name__)


class ExpirationWatcher:
    def __init__(
        self,
        connection_service: ConnectionService,
        interval_seconds: float = 1.0,
    ) -> None:
        self._connection_service = connection_service
        self._interval_seconds = interval_seconds
        self._task: asyncio.Task[None] | None = None
        self._stopped = False

    async def run_once(self) -> list[str]:
        return await self._connection_service.run_once()

    async def _loop(self) -> None:
        while not self._stopped:
            try:
                await self.run_once()
            except Exception as exc:
                logger.error("Ошибка при проверке просроченных соединений: %s", exc)
            try:
                await asyncio.sleep(self._interval_seconds)
            except asyncio.CancelledError:
                break

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._stopped = False
            self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._stopped = True
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
