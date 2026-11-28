from dataclasses import replace
from datetime import datetime
from uuid import UUID

from chats.app.domain import ChatRecord, ChatType, MemberRecord, MemberRole


class ConstraintViolationError(ValueError):
    """Signals a DB-equivalent uniqueness or check constraint violation in memory."""

    def __init__(self, constraint_name: str, message: str) -> None:
        self.constraint_name = constraint_name
        super().__init__(f"{constraint_name}: {message}")


def _validate_chat_constraints(chat: ChatRecord) -> None:
    if chat.type == ChatType.GROUP:
        if chat.title is None or len(chat.title) < 1 or chat.direct_key is not None:
            raise ConstraintViolationError(
                "ck_chats_group_fields",
                "Group chat requires non-empty title and null direct_key",
            )
    elif chat.type == ChatType.PERSONAL:
        if chat.title is not None or not chat.direct_key:
            raise ConstraintViolationError(
                "ck_chats_personal_fields",
                "Personal chat requires null title and non-null direct_key",
            )


class InMemoryMemberRepository:
    def __init__(self) -> None:
        self._members: dict[tuple[UUID, UUID], MemberRecord] = {}

    async def get_member(self, chat_id: UUID, user_id: UUID) -> MemberRecord | None:
        return self._members.get((chat_id, user_id))

    async def list_members(self, chat_id: UUID) -> list[MemberRecord]:
        items = [m for (cid, _), m in self._members.items() if cid == chat_id]
        return sorted(items, key=lambda m: (m.joined_at, str(m.user_id)))

    async def update_last_read(self, chat_id: UUID, user_id: UUID, last_read_at: datetime) -> bool:
        key = (chat_id, user_id)
        existing = self._members.get(key)
        if existing is None:
            return False
        self._members[key] = replace(existing, last_read_at=last_read_at)
        return True

    def add_member_sync(self, member: MemberRecord) -> MemberRecord:
        key = (member.chat_id, member.user_id)
        if key in self._members:
            raise ConstraintViolationError(
                "pk_chat_members",
                f"Member {member.user_id} already exists in chat {member.chat_id}",
            )
        if member.role == MemberRole.OWNER:
            has_owner = any(
                m.role == MemberRole.OWNER
                for (cid, _), m in self._members.items()
                if cid == member.chat_id
            )
            if has_owner:
                raise ConstraintViolationError(
                    "uq_chat_members_owner",
                    f"Chat {member.chat_id} already has an owner",
                )
        self._members[key] = member
        return member

    def delete_chat_members_sync(self, chat_id: UUID) -> None:
        keys = [key for key in self._members if key[0] == chat_id]
        for key in keys:
            del self._members[key]

    def list_user_memberships_sync(self, user_id: UUID) -> list[MemberRecord]:
        return [m for (_, uid), m in self._members.items() if uid == user_id]

    def clear(self) -> None:
        self._members.clear()


class InMemoryChatRepository:
    def __init__(self, member_repo: InMemoryMemberRepository | None = None) -> None:
        self._chats: dict[UUID, ChatRecord] = {}
        self._direct_index: dict[str, UUID] = {}
        self._member_repo = member_repo or InMemoryMemberRepository()

    @property
    def member_repo(self) -> InMemoryMemberRepository:
        return self._member_repo

    async def create_group(self, chat: ChatRecord, owner_member: MemberRecord) -> ChatRecord:
        if chat.id in self._chats:
            raise ConstraintViolationError("pk_chats", f"Chat {chat.id} already exists")
        if chat.type != ChatType.GROUP:
            raise ConstraintViolationError("ck_chats_type", "Expected group chat")
        if owner_member.chat_id != chat.id or owner_member.role != MemberRole.OWNER:
            raise ConstraintViolationError("uq_chat_members_owner", "Group must start with owner")
        _validate_chat_constraints(chat)

        self._chats[chat.id] = chat
        self._member_repo.add_member_sync(owner_member)
        return chat

    async def get_or_create_personal(
        self,
        chat: ChatRecord,
        members: tuple[MemberRecord, MemberRecord],
    ) -> tuple[ChatRecord, bool]:
        if chat.type != ChatType.PERSONAL:
            raise ConstraintViolationError("ck_chats_type", "Expected personal chat")
        _validate_chat_constraints(chat)
        assert chat.direct_key is not None

        existing_id = self._direct_index.get(chat.direct_key)
        if existing_id is not None:
            return self._chats[existing_id], False

        if chat.id in self._chats:
            raise ConstraintViolationError("pk_chats", f"Chat {chat.id} already exists")

        self._chats[chat.id] = chat
        self._direct_index[chat.direct_key] = chat.id
        try:
            for member in members:
                if member.chat_id != chat.id:
                    raise ConstraintViolationError(
                        "fk_chat_members_chat_id_chats", "Member chat_id mismatch"
                    )
                self._member_repo.add_member_sync(member)
        except Exception:
            self._member_repo.delete_chat_members_sync(chat.id)
            self._direct_index.pop(chat.direct_key, None)
            self._chats.pop(chat.id, None)
            raise
        return chat, True

    async def get_by_id(self, chat_id: UUID) -> ChatRecord | None:
        return self._chats.get(chat_id)

    async def get_by_direct_key(self, direct_key: str) -> ChatRecord | None:
        chat_id = self._direct_index.get(direct_key)
        if chat_id is None:
            return None
        return self._chats.get(chat_id)

    async def list_for_user(self, user_id: UUID) -> list[tuple[ChatRecord, MemberRecord]]:
        memberships = self._member_repo.list_user_memberships_sync(user_id)
        items: list[tuple[ChatRecord, MemberRecord]] = []
        for member in memberships:
            chat = self._chats.get(member.chat_id)
            if chat is not None:
                items.append((chat, member))
        items.sort(key=lambda pair: (pair[0].created_at, str(pair[0].id)), reverse=True)
        return items

    async def update_title(self, chat_id: UUID, title: str) -> ChatRecord | None:
        chat = self._chats.get(chat_id)
        if chat is None:
            return None
        updated = replace(chat, title=title)
        _validate_chat_constraints(updated)
        self._chats[chat_id] = updated
        return updated

    async def delete(self, chat_id: UUID) -> bool:
        chat = self._chats.pop(chat_id, None)
        if chat is None:
            return False
        if chat.direct_key is not None:
            self._direct_index.pop(chat.direct_key, None)
        self._member_repo.delete_chat_members_sync(chat_id)
        return True

    def clear(self) -> None:
        self._chats.clear()
        self._direct_index.clear()
        self._member_repo.clear()
