from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    USE_MOCKS: bool = True
    CHATS_SERVICE_URL: str = "http://chats:8000"
    USERS_SERVICE_URL: str = "http://users:8000"
    DEFAULT_PAGE_LIMIT: int = 30
    MAX_PAGE_LIMIT: int = 100

    class Config:
        env_file = ".env"


settings = Settings()
