from collections.abc import Sequence
from dataclasses import asdict
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database import translate_database_errors
from app.adapters.tables import users
from app.models import User
from app.ports.user_repository import ProfileChanges


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _fetch_one(self, statement: sa.Executable) -> User | None:
        with translate_database_errors():
            result = await self._session.execute(statement)
            row = result.mappings().one_or_none()
        return User(**row) if row is not None else None

    async def add(self, user: User) -> User:
        with translate_database_errors():
            await self._session.execute(sa.insert(users).values(**asdict(user)))
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self._fetch_one(sa.select(users).where(users.c.id == user_id))

    async def get_by_email(self, email: str) -> User | None:
        return await self._fetch_one(sa.select(users).where(users.c.email == email))

    async def get_by_phone(self, phone: str) -> User | None:
        return await self._fetch_one(sa.select(users).where(users.c.phone == phone))

    async def get_by_username(self, username: str) -> User | None:
        return await self._fetch_one(sa.select(users).where(users.c.username == username))

    async def get_by_ids(self, user_ids: Sequence[UUID]) -> list[User]:
        if not user_ids:
            return []
        with translate_database_errors():
            result = await self._session.execute(sa.select(users).where(users.c.id.in_(user_ids)))
            found = {row["id"]: User(**row) for row in result.mappings()}
        # Сохраняем порядок входного списка, отсутствующие ID пропускаем.
        return [found[user_id] for user_id in dict.fromkeys(user_ids) if user_id in found]

    async def update_profile(self, user_id: UUID, changes: ProfileChanges) -> User | None:
        if not changes:
            return await self.get_by_id(user_id)
        return await self._fetch_one(
            sa.update(users).where(users.c.id == user_id).values(**changes).returning(users)
        )

    async def update_avatar(self, user_id: UUID, avatar_key: str | None) -> User | None:
        return await self._fetch_one(
            sa.update(users)
            .where(users.c.id == user_id)
            .values(avatar_key=avatar_key)
            .returning(users)
        )
