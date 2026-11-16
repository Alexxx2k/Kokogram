import os
from dataclasses import dataclass

from gateway.app.routing.route_table import ServiceTarget


@dataclass(frozen=True)
class GatewayConfig:
    users_service_url: str = "http://users:8000"
    chats_service_url: str = "http://chats:8000"
    messages_service_url: str = "http://messages:8000"
    gif_service_url: str = "http://gif:8000"
    ssl_certfile: str | None = None
    ssl_keyfile: str | None = None

    @classmethod
    def from_env(cls) -> "GatewayConfig":
        return cls(
            users_service_url=os.getenv("USERS_SERVICE_URL", "http://users:8000"),
            chats_service_url=os.getenv("CHATS_SERVICE_URL", "http://chats:8000"),
            messages_service_url=os.getenv("MESSAGES_SERVICE_URL", "http://messages:8000"),
            gif_service_url=os.getenv("GIF_SERVICE_URL", "http://gif:8000"),
            ssl_certfile=os.getenv("SSL_CERTFILE") or os.getenv("SSL_CERT_PATH"),
            ssl_keyfile=os.getenv("SSL_KEYFILE") or os.getenv("SSL_KEY_PATH"),
        )

    def get_service_url(self, target: ServiceTarget) -> str:
        match target:
            case ServiceTarget.USERS:
                return self.users_service_url
            case ServiceTarget.CHATS:
                return self.chats_service_url
            case ServiceTarget.MESSAGES:
                return self.messages_service_url
            case ServiceTarget.GIF:
                return self.gif_service_url
