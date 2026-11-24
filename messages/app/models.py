from datetime import datetime
from typing import Literal

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


class MessageDTO(BaseModel):
    id: str
    chat_id: str
    author_id: str
    text: str | None
    entities: list[EntityDTO] | None
    created_at: datetime
    edited_at: datetime | None = None
    is_deleted: bool = False


class MessageListResponse(BaseModel):
    items: list[MessageDTO]
    next_cursor: str | None = None
