import os
from dataclasses import dataclass, field
from urllib.parse import quote


@dataclass(frozen=True)
class Settings:
    database_url: str = field(
        default="postgresql+psycopg://kokogram:kokogram@localhost:5432/kokogram", repr=False
    )
    s3_endpoint_url: str = "http://localhost:8333"
    s3_region: str = "us-east-1"
    s3_bucket: str = "kokogram"
    s3_access_key: str = field(default="", repr=False)
    s3_secret_key: str = field(default="", repr=False)
    url_signing_secret: str = field(default="", repr=False)
    signed_url_ttl_seconds: int = 15 * 60
    session_ttl_days: int = 30
    avatar_max_bytes: int = 5 * 1024 * 1024

    def __post_init__(self) -> None:
        if not 0 < self.signed_url_ttl_seconds <= 15 * 60:
            raise ValueError("SIGNED_URL_TTL_SECONDS должен быть от 1 до 900")
        if not 0 < self.session_ttl_days <= 30:
            raise ValueError("SESSION_TTL_DAYS должен быть от 1 до 30")
        if not 0 < self.avatar_max_bytes <= 5 * 1024 * 1024:
            raise ValueError("AVATAR_MAX_BYTES должен быть от 1 до 5242880")

    @classmethod
    def from_env(cls) -> "Settings":
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            user = quote(os.environ.get("POSTGRES_USER", "kokogram"), safe="")
            password = quote(os.environ.get("POSTGRES_PASSWORD", "kokogram"), safe="")
            host = os.environ.get("POSTGRES_HOST", "localhost")
            port = int(os.environ.get("POSTGRES_PORT", "5432"))
            database = quote(os.environ.get("POSTGRES_DB", "kokogram"), safe="")
            database_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"

        # Как и миграции, используем драйвер psycopg 3.
        for prefix in ("postgresql://", "postgres://"):
            if database_url.startswith(prefix):
                database_url = "postgresql+psycopg://" + database_url[len(prefix) :]
                break

        return cls(
            database_url=database_url,
            s3_endpoint_url=os.environ.get("S3_ENDPOINT_URL", "http://localhost:8333"),
            s3_region=os.environ.get("S3_REGION", "us-east-1"),
            s3_bucket=os.environ.get("S3_BUCKET", "kokogram"),
            s3_access_key=os.environ.get("S3_ACCESS_KEY", ""),
            s3_secret_key=os.environ.get("S3_SECRET_KEY", ""),
            url_signing_secret=os.environ.get("URL_SIGNING_SECRET", ""),
            signed_url_ttl_seconds=int(os.environ.get("SIGNED_URL_TTL_SECONDS", "900")),
            session_ttl_days=int(os.environ.get("SESSION_TTL_DAYS", "30")),
            avatar_max_bytes=int(os.environ.get("AVATAR_MAX_BYTES", "5242880")),
        )
