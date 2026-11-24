from typing import Literal

from fastapi import FastAPI, Header, Query
from kokogram_shared import SystemClock, UuidGenerator
from kokogram_shared.fastapi_handlers import register_error_handlers
from kokogram_shared.fastapi_middleware import setup_observability

from messages.app.adapters.chats_mock import MockChatsClient
from messages.app.adapters.event_publisher import RecordingPublisher
from messages.app.adapters.repo_memory import MemoryMessageRepository
from messages.app.adapters.users_mock import MockUsersClient
from messages.app.config import settings
from messages.app.message_policy import MessagePolicy
from messages.app.models import (
    EditMessageRequest,
    MessageDTO,
    MessageListResponse,
    SendMessageRequest,
)
from messages.app.services.message_service import MessageService

app = FastAPI(title="messages")
register_error_handlers(app)
setup_observability(app, service="messages")

clock = SystemClock()
id_generator = UuidGenerator()

repo = MemoryMessageRepository()
policy = MessagePolicy(clock=clock)
publisher = RecordingPublisher()

if settings.USE_MOCKS:
    chats_client = MockChatsClient()
    users_client = MockUsersClient()
else:
    chats_client = MockChatsClient()
    users_client = MockUsersClient()

message_service = MessageService(
    repo=repo,
    chats_client=chats_client,
    users_client=users_client,
    publisher=publisher,
    policy=policy,
    id_generator=id_generator,
    clock=clock,
)


@app.post("/chats/{chat_id}/messages", response_model=MessageDTO, status_code=201)
async def send_message(
    chat_id: str,
    request: SendMessageRequest,
    user_id: str = Header(..., alias="X-User-Id"),
) -> MessageDTO:
    return await message_service.send_message(chat_id, user_id, request)


@app.get("/chats/{chat_id}/messages", response_model=MessageListResponse)
async def get_history(
    chat_id: str,
    user_id: str = Header(..., alias="X-User-Id"),
    limit: int = Query(settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    before: str | None = Query(None),
) -> MessageListResponse:
    items, next_cursor = await message_service.get_history(chat_id, user_id, limit, before)
    return MessageListResponse(items=items, next_cursor=next_cursor)


@app.patch("/messages/{message_id}", response_model=MessageDTO)
async def edit_message(
    message_id: str,
    request: EditMessageRequest,
    user_id: str = Header(..., alias="X-User-Id"),
) -> MessageDTO:
    return await message_service.edit_message(message_id, user_id, request)


@app.delete("/messages/{message_id}", status_code=204)
async def delete_message(
    message_id: str,
    user_id: str = Header(..., alias="X-User-Id"),
    scope: Literal["all", "me"] = Query(...),
) -> None:
    await message_service.delete_message(message_id, user_id, scope)


@app.post("/chats/{chat_id}/read", status_code=204)
async def mark_read(
    chat_id: str,
    user_id: str = Header(..., alias="X-User-Id"),
) -> None:
    await message_service.mark_read(chat_id, user_id)
