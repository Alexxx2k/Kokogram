from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class User:
    id: UUID
    email: str | None
    phone: str | None
    password_hash: str = field(repr=False)
    username: str
    status: str | None
    avatar_key: str | None
    created_at: datetime


@dataclass(frozen=True)
class Session:
    id: UUID
    user_id: UUID
    token_hash: str = field(repr=False)
    expires_at: datetime
    created_at: datetime
