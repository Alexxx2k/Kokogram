from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class ChatType(StrEnum):
    PERSONAL = "personal"
    GROUP = "group"


class MemberRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


@dataclass(frozen=True)
class UserProfile:
    id: UUID
    username: str
    status: str | None = None
    avatar_url: str | None = None


@dataclass(frozen=True)
class ContactCheckResult:
    user_exists: bool
    is_contact: bool


@dataclass(frozen=True)
class ChatRecord:
    id: UUID
    type: ChatType
    title: str | None
    avatar_key: str | None
    direct_key: str | None
    created_at: datetime


@dataclass(frozen=True)
class MemberRecord:
    chat_id: UUID
    user_id: UUID
    role: MemberRole
    joined_at: datetime
    last_read_at: datetime | None = None


@dataclass(frozen=True)
class OwnerCandidate:
    user_id: UUID
    role: MemberRole
    username: str


@dataclass(frozen=True)
class ChatView:
    id: UUID
    type: ChatType
    title: str | None
    avatar_url: str | None
    peer: UserProfile | None
    my_role: MemberRole
    created_at: datetime


@dataclass(frozen=True)
class PersonalChatCreateResult:
    chat: ChatView
    created: bool


@dataclass(frozen=True)
class InternalPersonalChatResult:
    chat_id: UUID
    created: bool


@dataclass(frozen=True)
class MembershipInfo:
    is_member: bool
    chat_type: ChatType | None
    members: list[MemberRecord]


@dataclass(frozen=True)
class ChatEvent:
    event_id: UUID
    type: str
    occurred_at: datetime
    payload: dict[str, Any]
