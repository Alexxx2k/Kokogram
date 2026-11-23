from presence.app.ports.gateway_client import WsDelivery


class InMemoryGatewayClient:
    def __init__(self) -> None:
        self.deliveries: list[WsDelivery] = []

    async def deliver(self, deliveries: list[WsDelivery]) -> None:
        self.deliveries.extend(deliveries)

    def clear(self) -> None:
        self.deliveries.clear()
