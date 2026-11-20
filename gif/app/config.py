from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GIPHY_BASE_URL: str = "http://localhost:8090"
    GIPHY_TIMEOUT: float = 1.0
    CACHE_TTL_SEARCH: int = 300
    CACHE_TTL_CHECK: int = 3600
    DEFAULT_LIMIT: int = 20
    REDIS_URL: str = "redis://localhost:6379/0"
    ALLOWED_HOSTS: list[str] = [
        "localhost",
        "giphy-stub",
        "giphy.com",
        "media.giphy.com",
        "i.giphy.com",
    ]

    class Config:
        env_file = ".env"


settings = Settings()
