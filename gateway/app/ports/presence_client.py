from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class UserStatus:
    user_id: str
    online: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "online": self.online,
        }


class PresenceClient(Protocol):
    async def register_connection(self, connection_id: str, user_id: str) -> None: ...

    async def disconnect(self, connection_id: str) -> None: ...

    async def ping(self, connection_id: str) -> None: ...

    async def update_subscriptions(
        self,
        connection_id: str,
        add: list[str] | None = None,
        remove: list[str] | None = None,
    ) -> list[UserStatus]: ...
