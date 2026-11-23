import httpx

from presence.app.ports.gateway_client import WsDelivery


class HttpGatewayClient:
    def __init__(self, base_url: str, client: httpx.AsyncClient | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = client

    async def deliver(self, deliveries: list[WsDelivery]) -> None:
        if not deliveries:
            return
        payload = {"deliveries": [d.to_dict() for d in deliveries]}
        if self._client is not None:
            await self._client.post(f"{self.base_url}/internal/ws/deliver", json=payload)
        else:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                await client.post(f"{self.base_url}/internal/ws/deliver", json=payload)
