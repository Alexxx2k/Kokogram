from typing import Protocol

from chats.app.domain import ChatEvent


class EventPublisher(Protocol):
    async def publish(self, event: ChatEvent) -> None: ...
