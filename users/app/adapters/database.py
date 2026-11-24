from collections.abc import Iterator
from contextlib import contextmanager

from kokogram_shared import AppError, ErrorCode
from sqlalchemy.exc import IntegrityError, InterfaceError, OperationalError, TimeoutError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_UNIQUE_ERRORS = {
    "uq_users_email": ErrorCode.EMAIL_TAKEN,
    "uq_users_phone": ErrorCode.PHONE_TAKEN,
    "uq_users_username": ErrorCode.USERNAME_TAKEN,
}


@contextmanager
def translate_database_errors() -> Iterator[None]:
    try:
        yield
    except IntegrityError as exc:
        original = exc.orig
        diagnostic = getattr(original, "diag", None)
        constraint = getattr(diagnostic, "constraint_name", None)
        code = _UNIQUE_ERRORS.get(constraint)
        if getattr(original, "sqlstate", None) == "23505" and code is not None:
            raise AppError(code) from exc
        raise
    except (OperationalError, InterfaceError, TimeoutError) as exc:
        raise AppError(ErrorCode.SERVICE_UNAVAILABLE) from exc


class Database:
    def __init__(self, url: str) -> None:
        self.engine = create_async_engine(url, pool_pre_ping=True, hide_parameters=True)
        self.sessions = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    async def close(self) -> None:
        await self.engine.dispose()
