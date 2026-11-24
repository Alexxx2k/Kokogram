from datetime import datetime

from messages.app.models import MessageDTO
from messages.app.ports.message_repo import MessageRepository


class MemoryMessageRepository(MessageRepository):
    def __init__(self):
        self._messages: dict[str, MessageDTO] = {}
        self._chat_messages: dict[str, list[str]] = {}
        self._hidden: set[tuple[str, str]] = set()

    def _encode_cursor(self, message: MessageDTO) -> str:
        return f"{message.created_at.isoformat()}_{message.id}"

    def _decode_cursor(self, cursor: str) -> tuple[datetime, str]:
        time_str, msg_id = cursor.rsplit("_", 1)
        return datetime.fromisoformat(time_str), msg_id

    async def save(self, message: MessageDTO) -> None:
        self._messages[message.id] = message
        if message.chat_id not in self._chat_messages:
            self._chat_messages[message.chat_id] = []
        self._chat_messages[message.chat_id].append(message.id)

    async def get_by_id(self, message_id: str) -> MessageDTO | None:
        return self._messages.get(message_id)

    async def get_history(
        self, chat_id: str, user_id: str, limit: int, before_cursor: str | None
    ) -> tuple[list[MessageDTO], str | None]:
        chat_msg_ids = self._chat_messages.get(chat_id, [])
        messages = [self._messages[mid] for mid in chat_msg_ids]

        messages.sort(key=lambda m: (m.created_at, m.id), reverse=True)

        if before_cursor:
            cursor_time, cursor_id = self._decode_cursor(before_cursor)
            messages = [m for m in messages if (m.created_at, m.id) < (cursor_time, cursor_id)]

        messages = [m for m in messages if (user_id, m.id) not in self._hidden]

        has_next = len(messages) > limit
        result_messages = messages[:limit]

        next_cursor = None
        if has_next and result_messages:
            next_cursor = self._encode_cursor(result_messages[-1])

        return result_messages, next_cursor

    async def mark_deleted_for_all(self, message_id: str) -> None:
        if message_id in self._messages:
            msg = self._messages[message_id]
            msg.is_deleted = True
            msg.text = None
            msg.entities = None

    async def hide_for_user(self, message_id: str, user_id: str) -> None:
        self._hidden.add((user_id, message_id))
