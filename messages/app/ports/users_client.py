from typing import Protocol


class UsersClient(Protocol):
    async def check_blocked(self, user_a: str, user_b: str) -> bool: ...
