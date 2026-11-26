from datetime import datetime

from messages.app.models import MemberDTO, MembershipDTO


class MockChatsClient:
    def __init__(self):
        self._memberships = {
            "chat-123": {
                "chat_type": "personal",
                "members": [
                    MemberDTO(user_id="user-1", role="member", last_read_at=None),
                    MemberDTO(user_id="user-2", role="member", last_read_at=None),
                ],
            },
            "group-456": {
                "chat_type": "group",
                "members": [
                    MemberDTO(user_id="user-1", role="owner", last_read_at=None),
                    MemberDTO(user_id="user-3", role="member", last_read_at=None),
                ],
            },
        }

    async def check_membership(self, chat_id: str, user_id: str) -> MembershipDTO:
        chat = self._memberships.get(chat_id)
        if not chat:
            return MembershipDTO(is_member=False, chat_type="unknown", members=[])

        is_member = any(m.user_id == user_id for m in chat["members"])
        return MembershipDTO(
            is_member=is_member,
            chat_type=chat["chat_type"],
            members=chat["members"],
        )

    async def update_last_read(self, chat_id: str, user_id: str, last_read_at: datetime) -> None:
        chat = self._memberships.get(chat_id)
        if chat:
            for m in chat["members"]:
                if m.user_id == user_id:
                    m.last_read_at = last_read_at
