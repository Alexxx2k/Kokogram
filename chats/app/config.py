import os
from dataclasses import dataclass


def _normalize_async_database_url(url: str) -> str:
    for prefix in ("postgresql+psycopg://", "postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+asyncpg://" + url[len(prefix) :]
    return url


def _default_database_url() -> str:
    user = os.getenv("POSTGRES_USER", "kokogram")
    password = os.getenv("POSTGRES_PASSWORD", "kokogram")
    default_host = "postgres" if os.path.exists("/.dockerenv") else "localhost"
    host = os.getenv("POSTGRES_HOST", default_host)
    port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "kokogram")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}"


def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() in ("true", "1", "yes")


@dataclass(frozen=True)
class ChatsConfig:
    database_url: str = "postgresql+asyncpg://kokogram:kokogram@localhost:5432/kokogram"
    users_service_url: str = "http://users:8000"
    url_signer_secret: str = "kokogram-dev-secret"
    avatar_url_ttl_seconds: int = 900
    use_in_memory_repos: bool = False
    use_mock_users_client: bool = False
    use_recording_event_publisher: bool = False

    @classmethod
    def from_env(cls) -> "ChatsConfig":
        raw_db_url = os.getenv("DATABASE_URL")
        if raw_db_url:
            use_in_memory = raw_db_url == "mock" or _env_flag("USE_IN_MEMORY_REPOS")
            database_url = (
                "mock" if raw_db_url == "mock" else _normalize_async_database_url(raw_db_url)
            )
        else:
            use_in_memory = _env_flag("USE_IN_MEMORY_REPOS")
            database_url = _default_database_url()

        users_service_url = os.getenv("USERS_SERVICE_URL", "http://users:8000")
        use_mock_users = users_service_url == "mock" or _env_flag("USE_MOCK_USERS_CLIENT")

        return cls(
            database_url=database_url,
            users_service_url=users_service_url,
            url_signer_secret=os.getenv("URL_SIGNER_SECRET", "kokogram-dev-secret"),
            avatar_url_ttl_seconds=int(os.getenv("AVATAR_URL_TTL_SECONDS", "900")),
            use_in_memory_repos=use_in_memory,
            use_mock_users_client=use_mock_users,
            use_recording_event_publisher=_env_flag("USE_RECORDING_EVENT_PUBLISHER"),
        )
