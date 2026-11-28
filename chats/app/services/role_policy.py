from collections.abc import Sequence
from uuid import UUID

from kokogram_shared.errors import AppError, ErrorCode, ValidationReason

from chats.app.domain import MemberRole, OwnerCandidate

MIN_GROUP_TITLE_LENGTH = 1
MAX_GROUP_TITLE_LENGTH = 20


class RolePolicy:
    """Pure role and group-validation rules without external dependencies (HLD §5.1)."""

    @staticmethod
    def validate_title(title: str) -> str:
        normalized = title.strip()
        if not (MIN_GROUP_TITLE_LENGTH <= len(normalized) <= MAX_GROUP_TITLE_LENGTH):
            raise AppError.validation(ValidationReason.TITLE_LENGTH, field="title")
        return normalized

    @staticmethod
    def can_edit_group(role: MemberRole | None) -> bool:
        return role in (MemberRole.OWNER, MemberRole.ADMIN)

    @classmethod
    def require_edit_group(cls, role: MemberRole | None) -> None:
        if not cls.can_edit_group(role):
            raise AppError(ErrorCode.FORBIDDEN)

    @staticmethod
    def can_delete_group(role: MemberRole | None) -> bool:
        return role == MemberRole.OWNER

    @classmethod
    def require_delete_group(cls, role: MemberRole | None) -> None:
        if not cls.can_delete_group(role):
            raise AppError(ErrorCode.FORBIDDEN)

    @staticmethod
    def can_change_role(
        actor_role: MemberRole | None,
        target_role: MemberRole | None = None,
    ) -> bool:
        if actor_role != MemberRole.OWNER:
            return False
        if target_role == MemberRole.OWNER:
            return False
        return True

    @classmethod
    def require_change_role(
        cls,
        actor_role: MemberRole | None,
        target_role: MemberRole | None = None,
    ) -> None:
        if not cls.can_change_role(actor_role, target_role):
            raise AppError(ErrorCode.FORBIDDEN)

    @staticmethod
    def can_remove_member(
        actor_role: MemberRole | None,
        target_role: MemberRole | None,
    ) -> bool:
        if actor_role == MemberRole.OWNER:
            return target_role in (MemberRole.ADMIN, MemberRole.MEMBER)
        if actor_role == MemberRole.ADMIN:
            return target_role == MemberRole.MEMBER
        return False

    @classmethod
    def require_remove_member(
        cls,
        actor_role: MemberRole | None,
        target_role: MemberRole | None,
    ) -> None:
        if not cls.can_remove_member(actor_role, target_role):
            raise AppError(ErrorCode.FORBIDDEN)

    @staticmethod
    def select_new_owner(candidates: Sequence[OwnerCandidate]) -> UUID | None:
        admins = [c for c in candidates if c.role == MemberRole.ADMIN]
        pool = admins or [c for c in candidates if c.role == MemberRole.MEMBER]
        if not pool:
            return None
        chosen = min(pool, key=lambda c: (c.username.casefold(), c.username, str(c.user_id)))
        return chosen.user_id
