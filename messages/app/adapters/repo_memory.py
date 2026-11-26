import base64
import json
from datetime import datetime

from messages.app.api.schemas import MessageDTO


class MemoryMessageRepository:
    def __init__(self):
        self._messages: dict[str, MessageDTO] = {}
        self._chat_messages: dict[str, list[str]] = {}
        self._hidden: set[tuple[str, str]] = set()

    def _encode_cursor(self, message: MessageDTO) -> str:
        time_str = message.created_at.isoformat()
        if time_str.endswith("+00:00"):
            time_str = time_str[:-6] + "Z"

        raw_data = json.dumps({"t": time_str, "id": message.id})
        return base64.urlsafe_b64encode(raw_data.encode()).decode()

    def _decode_cursor(self, cursor: str) -> tuple[datetime, str]:
        from kokogram_shared import AppError, ErrorCode

        try:
            decoded = base64.urlsafe_b64decode(cursor.encode()).decode()
            data = json.loads(decoded)

            time_str = data["t"]
            if time_str.endswith("Z"):
                time_str = time_str[:-1] + "+00:00"

            return datetime.fromisoformat(time_str), data["id"]
        except (ValueError, KeyError, TypeError, base64.binascii.Error):
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                details=[{"field": "before", "reason": "invalid_cursor"}],
            )

    async def save(self, message: MessageDTO) -> None:
        is_new = message.id not in self._messages

        self._messages[message.id] = message.model_copy(deep=True)

        if is_new:
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
            message = self._messages.pop(message_id)

            chat_ids = self._chat_messages.get(message.chat_id, [])
            if message_id in chat_ids:
                chat_ids.remove(message_id)

            self._hidden = {(uid, mid) for uid, mid in self._hidden if mid != message_id}

            for msg in self._messages.values():
                if msg.reply_to_id == message_id:
                    msg.reply_to_id = None

    async def hide_for_user(self, message_id: str, user_id: str) -> None:
        self._hidden.add((user_id, message_id))
