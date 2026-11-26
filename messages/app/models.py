from datetime import datetime

from pydantic import BaseModel


class MemberDTO(BaseModel):
    user_id: str
    role: str
    last_read_at: datetime | None = None


class MembershipDTO(BaseModel):
    is_member: bool
    chat_type: str
    members: list[MemberDTO] = []
