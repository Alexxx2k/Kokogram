from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    USE_MOCKS: bool = True
    CHATS_SERVICE_URL: str = "http://localhost:8081"
    USERS_SERVICE_URL: str = "http://localhost:8082"
    DEFAULT_PAGE_LIMIT: int = 30
    MAX_PAGE_LIMIT: int = 100

    class Config:
        env_file = ".env"


settings = Settings()
