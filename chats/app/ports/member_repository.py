from datetime import datetime
from typing import Protocol
from uuid import UUID

from chats.app.domain import MemberRecord


class MemberRepository(Protocol):
    async def get_member(self, chat_id: UUID, user_id: UUID) -> MemberRecord | None: ...

    async def list_members(self, chat_id: UUID) -> list[MemberRecord]: ...

    async def update_last_read(
        self, chat_id: UUID, user_id: UUID, last_read_at: datetime
    ) -> bool: ...
