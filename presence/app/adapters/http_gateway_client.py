import logging

import httpx
from kokogram_shared.errors import AppError, ErrorCode
from kokogram_shared.logging import get_request_id

from presence.app.ports.gateway_client import WsDelivery

logger = logging.getLogger(__name__)


class HttpGatewayClient:
    def __init__(
        self,
        base_url: str,
        client: httpx.AsyncClient | None = None,
        timeout: float = 5.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = client
        self._timeout = timeout

    async def deliver(self, deliveries: list[WsDelivery]) -> None:
        if not deliveries:
            return
        payload = {"deliveries": [d.to_dict() for d in deliveries]}
        headers: dict[str, str] = {}
        request_id = get_request_id()
        if request_id:
            headers["X-Request-ID"] = request_id

        client = self._client or httpx.AsyncClient(timeout=httpx.Timeout(self._timeout))
        should_close = self._client is None
        try:
            response = await client.post(
                f"{self.base_url}/internal/ws/deliver",
                json=payload,
                headers=headers,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            logger.warning(
                "Ошибка доставки WS-сообщений в Gateway: %s",
                exc,
                extra={"error_code": str(ErrorCode.SERVICE_UNAVAILABLE)},
            )
            raise AppError(ErrorCode.SERVICE_UNAVAILABLE) from exc
        finally:
            if should_close:
                await client.aclose()
