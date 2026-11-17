from typing import Annotated

from fastapi import Depends
from kokogram_shared import (
    Clock,
    IdGenerator,
    SecretsTokenGenerator,
    SystemClock,
    TokenGenerator,
    UrlSigner,
    UuidGenerator,
)

from app.config import Settings


def get_settings() -> Settings:
    return Settings.from_env()


def get_clock() -> Clock:
    return SystemClock()


def get_id_generator() -> IdGenerator:
    return UuidGenerator()


def get_token_generator() -> TokenGenerator:
    return SecretsTokenGenerator()


def get_url_signer(
    settings: Annotated[Settings, Depends(get_settings)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> UrlSigner:
    if not settings.url_signing_secret:
        raise ValueError("Для подписанных ссылок задайте URL_SIGNING_SECRET")
    return UrlSigner(
        secret=settings.url_signing_secret,
        clock=clock,
        ttl=settings.signed_url_ttl_seconds,
    )
