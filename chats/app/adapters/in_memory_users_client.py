from collections.abc import Sequence
from uuid import UUID

from chats.app.domain import ContactCheckResult, UserProfile


class InMemoryUsersClient:
    def __init__(
        self,
        users: Sequence[UserProfile] | None = None,
        contacts: Sequence[tuple[UUID, UUID]] | None = None,
    ) -> None:
        self._users: dict[UUID, UserProfile] = {u.id: u for u in (users or ())}
        self._contacts: set[tuple[UUID, UUID]] = set(contacts or ())
        self.fail_with: Exception | None = None

    def add_user(self, profile: UserProfile) -> None:
        self._users[profile.id] = profile

    def add_contact(self, owner_id: UUID, user_id: UUID) -> None:
        self._contacts.add((owner_id, user_id))

    def set_failure(self, exc: Exception | None) -> None:
        self.fail_with = exc

    def clear(self) -> None:
        self._users.clear()
        self._contacts.clear()
        self.fail_with = None

    async def get_users(self, user_ids: Sequence[UUID]) -> dict[UUID, UserProfile]:
        if self.fail_with is not None:
            raise self.fail_with
        return {uid: self._users[uid] for uid in user_ids if uid in self._users}

    async def check_contact(self, owner_id: UUID, user_id: UUID) -> ContactCheckResult:
        if self.fail_with is not None:
            raise self.fail_with
        return ContactCheckResult(
            user_exists=user_id in self._users,
            is_contact=(owner_id, user_id) in self._contacts,
        )
