import httpx
from kokogram_shared.errors import AppError, ErrorCode
from kokogram_shared.logging import get_request_id

from gateway.app.ports.presence_client import PresenceClient, UserStatus


class HttpPresenceClient(PresenceClient):
    def __init__(
        self,
        base_url: str,
        client: httpx.AsyncClient | None = None,
        timeout: float = 5.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        request_id = get_request_id()
        if request_id:
            headers["X-Request-ID"] = request_id
        return headers

    async def register_connection(self, connection_id: str, user_id: str) -> None:
        url = f"{self._base_url}/internal/presence/connections"
        client = self._client or httpx.AsyncClient()
        should_close = self._client is None
        try:
            response = await client.post(
                url,
                json={"connection_id": connection_id, "user_id": str(user_id)},
                headers=self._headers(),
                timeout=self._timeout,
            )
            if 200 <= response.status_code < 300:
                return
            raise AppError(ErrorCode.SERVICE_UNAVAILABLE)
        except httpx.RequestError as exc:
            raise AppError(ErrorCode.SERVICE_UNAVAILABLE) from exc
        finally:
            if should_close:
                await client.aclose()

    async def disconnect(self, connection_id: str) -> None:
        url = f"{self._base_url}/internal/presence/connections/{connection_id}"
        client = self._client or httpx.AsyncClient()
        should_close = self._client is None
        try:
            response = await client.delete(
                url,
                headers=self._headers(),
                timeout=self._timeout,
            )
            if 200 <= response.status_code < 300:
                return
            raise AppError(ErrorCode.SERVICE_UNAVAILABLE)
        except httpx.RequestError as exc:
            raise AppError(ErrorCode.SERVICE_UNAVAILABLE) from exc
        finally:
            if should_close:
                await client.aclose()

    async def ping(self, connection_id: str) -> None:
        url = f"{self._base_url}/internal/presence/connections/{connection_id}/ping"
        client = self._client or httpx.AsyncClient()
        should_close = self._client is None
        try:
            response = await client.post(
                url,
                headers=self._headers(),
                timeout=self._timeout,
            )
            if 200 <= response.status_code < 300:
                return
            if response.status_code == 404:
                raise AppError(ErrorCode.NOT_FOUND, "Соединение не найдено")
            raise AppError(ErrorCode.SERVICE_UNAVAILABLE)
        except httpx.RequestError as exc:
            raise AppError(ErrorCode.SERVICE_UNAVAILABLE) from exc
        finally:
            if should_close:
                await client.aclose()

    async def update_subscriptions(
        self,
        connection_id: str,
        add: list[str] | None = None,
        remove: list[str] | None = None,
    ) -> list[UserStatus]:
        url = f"{self._base_url}/internal/presence/connections/{connection_id}/subscriptions"
        client = self._client or httpx.AsyncClient()
        should_close = self._client is None
        try:
            response = await client.put(
                url,
                json={"add": list(add or []), "remove": list(remove or [])},
                headers=self._headers(),
                timeout=self._timeout,
            )
            if response.status_code == 200:
                try:
                    data = response.json()
                    if not isinstance(data, dict):
                        raise ValueError("Ответ presence не является JSON-объектом")
                    raw_statuses = data.get("statuses", [])
                    if not isinstance(raw_statuses, list):
                        raise ValueError("Поле statuses должно быть списком")
                    statuses: list[UserStatus] = []
                    for item in raw_statuses:
                        if not isinstance(item, dict) or item.get("user_id") is None:
                            raise ValueError("Некорректный элемент в statuses")
                        statuses.append(
                            UserStatus(
                                user_id=str(item["user_id"]),
                                online=bool(item["online"]),
                            )
                        )
                    return statuses
                except (ValueError, KeyError, TypeError, AttributeError) as exc:
                    raise AppError(ErrorCode.SERVICE_UNAVAILABLE) from exc
            if response.status_code == 404:
                raise AppError(ErrorCode.NOT_FOUND, "Соединение не найдено")
            raise AppError(ErrorCode.SERVICE_UNAVAILABLE)
        except httpx.RequestError as exc:
            raise AppError(ErrorCode.SERVICE_UNAVAILABLE) from exc
        finally:
            if should_close:
                await client.aclose()
