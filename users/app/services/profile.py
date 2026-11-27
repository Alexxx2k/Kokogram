from collections.abc import Mapping, Sequence
from uuid import UUID

from kokogram_shared import AppError, ErrorCode

from app.models import User
from app.ports.user_repository import ProfileChanges, UserRepository
from app.validators import validate_status, validate_username


class ProfileService:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def get(self, user_id: UUID) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise AppError(ErrorCode.NOT_FOUND)
        return user

    async def update(self, user_id: UUID, updates: Mapping[str, str | None]) -> User:
        changes: ProfileChanges = {}
        if "username" in updates:
            changes["username"] = validate_username(updates["username"])
        if "status" in updates:
            changes["status"] = validate_status(updates["status"])
        user = await self._users.update_profile(user_id, changes)
        if user is None:
            raise AppError(ErrorCode.NOT_FOUND)
        return user

    async def search(self, username: str) -> list[User]:
        username = validate_username(username)
        user = await self._users.get_by_username(username)
        return [user] if user is not None else []

    async def get_many(self, user_ids: Sequence[UUID]) -> list[User]:
        if not 1 <= len(user_ids) <= 100:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                details=[{"field": "ids", "reason": "list_length"}],
            )
        return await self._users.get_by_ids(user_ids)
