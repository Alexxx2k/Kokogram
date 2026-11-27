from dataclasses import asdict

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database import translate_database_errors
from app.adapters.tables import sessions
from app.models import Session


class SqlAlchemySessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, session: Session) -> Session:
        with translate_database_errors():
            await self._session.execute(sa.insert(sessions).values(**asdict(session)))
        return session

    async def get_by_token_hash(self, token_hash: str) -> Session | None:
        with translate_database_errors():
            result = await self._session.execute(
                sa.select(sessions).where(sessions.c.token_hash == token_hash)
            )
            row = result.mappings().one_or_none()
        return Session(**row) if row is not None else None

    async def delete_by_token_hash(self, token_hash: str) -> None:
        with translate_database_errors():
            await self._session.execute(
                sa.delete(sessions).where(sessions.c.token_hash == token_hash)
            )
