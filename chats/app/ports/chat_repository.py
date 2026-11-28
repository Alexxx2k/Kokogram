from typing import Protocol
from uuid import UUID

from chats.app.domain import ChatRecord, MemberRecord


class ChatRepository(Protocol):
    async def create_group(self, chat: ChatRecord, owner_member: MemberRecord) -> ChatRecord: ...

    async def get_or_create_personal(
        self,
        chat: ChatRecord,
        members: tuple[MemberRecord, MemberRecord],
    ) -> tuple[ChatRecord, bool]: ...

    async def get_by_id(self, chat_id: UUID) -> ChatRecord | None: ...

    async def get_by_direct_key(self, direct_key: str) -> ChatRecord | None: ...

    async def list_for_user(self, user_id: UUID) -> list[tuple[ChatRecord, MemberRecord]]: ...

    async def update_title(self, chat_id: UUID, title: str) -> ChatRecord | None: ...

    async def delete(self, chat_id: UUID) -> bool: ...
