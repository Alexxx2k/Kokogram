from collections.abc import AsyncIterator
from datetime import timedelta
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from kokogram_shared import (
    AppError,
    Clock,
    ErrorCode,
    IdGenerator,
    SecretsTokenGenerator,
    SystemClock,
    TokenGenerator,
    UrlSigner,
    UuidGenerator,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database import translate_database_errors
from app.adapters.password_hasher import BcryptPasswordHasher
from app.adapters.session_repository import SqlAlchemySessionRepository
from app.adapters.user_repository import SqlAlchemyUserRepository
from app.config import Settings
from app.models import User
from app.ports.password_hasher import PasswordHasher
from app.ports.session_repository import SessionRepository
from app.ports.user_repository import UserRepository
from app.services.auth import AuthService
from app.services.profile import ProfileService
from app.services.sessions import SessionService

_bearer = HTTPBearer(auto_error=False)


def get_settings() -> Settings:
    return Settings.from_env()


async def get_database_session(request: Request) -> AsyncIterator[AsyncSession]:
    with translate_database_errors():
        async with request.app.state.database.sessions() as session, session.begin():
            yield session


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_database_session, scope="function")],
) -> UserRepository:
    return SqlAlchemyUserRepository(session)


def get_session_repository(
    session: Annotated[AsyncSession, Depends(get_database_session, scope="function")],
) -> SessionRepository:
    return SqlAlchemySessionRepository(session)


def get_clock() -> Clock:
    return SystemClock()


def get_id_generator() -> IdGenerator:
    return UuidGenerator()


def get_token_generator() -> TokenGenerator:
    return SecretsTokenGenerator()


def get_password_hasher() -> PasswordHasher:
    return BcryptPasswordHasher()


def get_profile_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
) -> ProfileService:
    return ProfileService(users)


def get_session_service(
    sessions: Annotated[SessionRepository, Depends(get_session_repository)],
    clock: Annotated[Clock, Depends(get_clock)],
    id_generator: Annotated[IdGenerator, Depends(get_id_generator)],
    token_generator: Annotated[TokenGenerator, Depends(get_token_generator)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SessionService:
    return SessionService(
        sessions, clock, id_generator, token_generator, timedelta(days=settings.session_ttl_days)
    )


def get_auth_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    clock: Annotated[Clock, Depends(get_clock)],
    id_generator: Annotated[IdGenerator, Depends(get_id_generator)],
    sessions: Annotated[SessionService, Depends(get_session_service)],
) -> AuthService:
    return AuthService(users, password_hasher, clock, id_generator, sessions)


def get_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> str:
    if credentials is None or not credentials.credentials.strip():
        raise AppError(ErrorCode.UNAUTHORIZED)
    return credentials.credentials


async def get_current_user(
    token: Annotated[str, Depends(get_bearer_token)],
    sessions: Annotated[SessionService, Depends(get_session_service)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    user_id = await sessions.verify(token)
    user = await users.get_by_id(user_id)
    if user is None:
        raise AppError(ErrorCode.UNAUTHORIZED)
    return user


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
