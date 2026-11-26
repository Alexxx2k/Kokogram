from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class EntityDTO(BaseModel):
    type: Literal["bold", "italic", "strike"]
    offset: int = Field(ge=0)
    length: int = Field(gt=0)


class SendMessageRequest(BaseModel):
    text: str | None = None
    entities: list[EntityDTO] | None = None
    reply_to_id: str | None = None


class EditMessageRequest(BaseModel):
    text: str | None = None
    entities: list[EntityDTO] | None = None


class ReplyToDTO(BaseModel):
    message_id: str | None = None
    sender_id: str | None = None
    text_preview: str | None = None
    deleted: bool = False


class MessageDTO(BaseModel):
    id: str
    chat_id: str
    sender_id: str
    text: str | None
    entities: list[EntityDTO] = []
    reply_to: ReplyToDTO | None = None
    attachment: Any | None = None
    status: str | None = None
    created_at: datetime
    edited_at: datetime | None = None
    is_reply: bool = False
    reply_to_id: str | None = None


class MessageListResponse(BaseModel):
    items: list[MessageDTO]
    next_cursor: str | None = None
