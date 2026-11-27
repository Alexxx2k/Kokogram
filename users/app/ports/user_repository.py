from collections.abc import Sequence
from typing import Protocol, TypedDict
from uuid import UUID

from app.models import User


class ProfileChanges(TypedDict, total=False):
    username: str
    status: str | None


class UserRepository(Protocol):
    async def add(self, user: User) -> User: ...

    async def get_by_id(self, user_id: UUID) -> User | None: ...

    async def get_by_id_for_update(self, user_id: UUID) -> User | None: ...

    async def get_by_email(self, email: str) -> User | None: ...

    async def get_by_phone(self, phone: str) -> User | None: ...

    async def get_by_username(self, username: str) -> User | None: ...

    async def get_by_ids(self, user_ids: Sequence[UUID]) -> list[User]: ...

    async def update_profile(self, user_id: UUID, changes: ProfileChanges) -> User | None: ...

    async def update_avatar(self, user_id: UUID, avatar_key: str | None) -> User | None: ...
