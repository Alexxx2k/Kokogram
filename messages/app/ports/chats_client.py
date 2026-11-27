from datetime import datetime
from typing import Protocol

from messages.app.models import MembershipDTO


class ChatsClient(Protocol):
    async def check_membership(self, chat_id: str, user_id: str) -> MembershipDTO: ...
    async def update_last_read(
        self, chat_id: str, user_id: str, last_read_at: datetime
    ) -> None: ...
