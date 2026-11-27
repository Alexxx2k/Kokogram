from typing import Literal

from fastapi import APIRouter, Depends, Header, Query

from messages.app.api.dependencies import get_message_service
from messages.app.api.schemas import (
    EditMessageRequest,
    MessageDTO,
    MessageListResponse,
    SendMessageRequest,
)
from messages.app.config import settings
from messages.app.services.message_service import MessageService

router = APIRouter()


@router.post("/chats/{chat_id}/messages", response_model=MessageDTO, status_code=201)
async def send_message(
    chat_id: str,
    request: SendMessageRequest,
    user_id: str = Header(..., alias="X-User-Id"),
    service: MessageService = Depends(get_message_service),
) -> MessageDTO:
    return await service.send_message(chat_id, user_id, request)


@router.get("/chats/{chat_id}/messages", response_model=MessageListResponse)
async def get_history(
    chat_id: str,
    user_id: str = Header(..., alias="X-User-Id"),
    limit: int = Query(settings.DEFAULT_PAGE_LIMIT, ge=1, le=settings.MAX_PAGE_LIMIT),
    before: str | None = Query(None),
    service: MessageService = Depends(get_message_service),
) -> MessageListResponse:
    items, next_cursor = await service.get_history(chat_id, user_id, limit, before)
    return MessageListResponse(items=items, next_cursor=next_cursor)


@router.patch("/messages/{message_id}", response_model=MessageDTO)
async def edit_message(
    message_id: str,
    request: EditMessageRequest,
    user_id: str = Header(..., alias="X-User-Id"),
    service: MessageService = Depends(get_message_service),
) -> MessageDTO:
    return await service.edit_message(message_id, user_id, request)


@router.delete("/messages/{message_id}", status_code=204)
async def delete_message(
    message_id: str,
    user_id: str = Header(..., alias="X-User-Id"),
    scope: Literal["all", "me"] = Query(...),
    service: MessageService = Depends(get_message_service),
) -> None:
    await service.delete_message(message_id, user_id, scope)


@router.post("/chats/{chat_id}/read", status_code=204)
async def mark_read(
    chat_id: str,
    user_id: str = Header(..., alias="X-User-Id"),
    service: MessageService = Depends(get_message_service),
) -> None:
    await service.mark_read(chat_id, user_id)
