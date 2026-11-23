import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PresenceConfig:
    redis_url: str = "redis://localhost:6379/0"
    connection_ttl_seconds: int = 75
    gateway_url: str = "http://gateway:8000"
    use_in_memory_store: bool = False
    use_mock_gateway: bool = True

    @classmethod
    def from_env(cls) -> "PresenceConfig":
        default_redis = (
            "redis://redis:6379/0" if os.path.exists("/.dockerenv") else "redis://localhost:6379/0"
        )
        redis_url = os.getenv("REDIS_URL", default_redis)
        use_in_memory = (
            os.getenv("USE_IN_MEMORY_PRESENCE_STORE", "false").lower() in ("true", "1")
            or redis_url == "mock"
        )
        use_mock_gw = os.getenv("USE_MOCK_GATEWAY_CLIENT", "true").lower() in ("true", "1")
        ttl_seconds = int(os.getenv("CONNECTION_TTL_SECONDS", "75"))

        return cls(
            redis_url=redis_url,
            connection_ttl_seconds=ttl_seconds,
            gateway_url=os.getenv("GATEWAY_URL", "http://gateway:8000"),
            use_in_memory_store=use_in_memory,
            use_mock_gateway=use_mock_gw,
        )
