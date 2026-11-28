from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from chats.app.domain import ContactCheckResult, UserProfile


class UsersClient(Protocol):
    async def get_users(self, user_ids: Sequence[UUID]) -> dict[UUID, UserProfile]: ...

    async def check_contact(self, owner_id: UUID, user_id: UUID) -> ContactCheckResult: ...
