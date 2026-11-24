from typing import Protocol

from app.models import Session


class SessionRepository(Protocol):
    async def add(self, session: Session) -> Session: ...

    async def get_by_token_hash(self, token_hash: str) -> Session | None: ...

    async def delete_by_token_hash(self, token_hash: str) -> None: ...
