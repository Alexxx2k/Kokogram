from typing import Protocol


class UsersClient(Protocol):
    async def verify_session(self, token: str) -> str | None: ...
