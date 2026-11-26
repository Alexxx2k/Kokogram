from functools import lru_cache

from fastapi import Depends
from kokogram_shared import SystemClock, UuidGenerator

from messages.app.adapters.chats_mock import MockChatsClient
from messages.app.adapters.event_publisher import RecordingPublisher
from messages.app.adapters.repo_memory import MemoryMessageRepository
from messages.app.adapters.users_mock import MockUsersClient
from messages.app.config import settings
from messages.app.services.message_policy import MessagePolicy
from messages.app.services.message_service import MessageService


def get_clock() -> SystemClock:
    return SystemClock()


def get_id_generator() -> UuidGenerator:
    return UuidGenerator()


@lru_cache
def get_repo() -> MemoryMessageRepository:
    return MemoryMessageRepository()


def get_policy(clock: SystemClock = Depends(get_clock)) -> MessagePolicy:
    return MessagePolicy(clock=clock)


def get_publisher(
    clock: SystemClock = Depends(get_clock),
    id_generator: UuidGenerator = Depends(get_id_generator),
) -> RecordingPublisher:
    return RecordingPublisher(clock=clock, id_generator=id_generator)


@lru_cache
def get_chats_client_singleton():
    return MockChatsClient()


@lru_cache
def get_users_client_singleton():
    return MockUsersClient()


def get_chats_client():
    if settings.USE_MOCKS:
        return get_chats_client_singleton()
    raise NotImplementedError("Real HttpChatsClient is not implemented yet")


def get_users_client():
    if settings.USE_MOCKS:
        return get_users_client_singleton()
    raise NotImplementedError("Real HttpUsersClient is not implemented yet")


def get_message_service(
    repo: MemoryMessageRepository = Depends(get_repo),
    chats_client=Depends(get_chats_client),
    users_client=Depends(get_users_client),
    publisher: RecordingPublisher = Depends(get_publisher),
    policy: MessagePolicy = Depends(get_policy),
    id_generator: UuidGenerator = Depends(get_id_generator),
    clock: SystemClock = Depends(get_clock),
) -> MessageService:
    return MessageService(
        repo=repo,
        chats_client=chats_client,
        users_client=users_client,
        publisher=publisher,
        policy=policy,
        id_generator=id_generator,
        clock=clock,
    )
