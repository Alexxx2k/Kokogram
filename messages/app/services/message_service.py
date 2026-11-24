from kokogram_shared import AppError, Clock, ErrorCode, IdGenerator

from messages.app.message_policy import MessagePolicy
from messages.app.models import (
    EditMessageRequest,
    MessageDTO,
    SendMessageRequest,
)
from messages.app.ports.chats_client import ChatsClient
from messages.app.ports.event_publisher import EventPublisher
from messages.app.ports.message_repo import MessageRepository
from messages.app.ports.users_client import UsersClient


class MessageService:
    def __init__(
        self,
        repo: MessageRepository,
        chats_client: ChatsClient,
        users_client: UsersClient,
        publisher: EventPublisher,
        policy: MessagePolicy,
        id_generator: IdGenerator,
        clock: Clock,
    ):
        self.repo = repo
        self.chats_client = chats_client
        self.users_client = users_client
        self.publisher = publisher
        self.policy = policy
        self.id_generator = id_generator
        self.clock = clock

    async def send_message(
        self, chat_id: str, user_id: str, request: SendMessageRequest
    ) -> MessageDTO:
        self.policy.validate_content(request.text, request.entities)

        is_member = await self.chats_client.check_membership(chat_id, user_id)
        if not is_member:
            raise AppError(ErrorCode.NOT_MEMBER)

        is_blocked = await self.users_client.check_blocked(user_id, "other_user")
        if is_blocked:
            raise AppError(ErrorCode.BLOCKED)

        message = MessageDTO(
            id=str(self.id_generator.new_id()),
            chat_id=chat_id,
            author_id=user_id,
            text=request.text,
            entities=request.entities,
            created_at=self.clock.now(),
            edited_at=None,
            is_deleted=False,
        )

        await self.repo.save(message)

        await self.publisher.publish(
            "message.created",
            {"message_id": message.id, "chat_id": chat_id, "author_id": user_id},
        )

        return message

    async def get_history(
        self, chat_id: str, user_id: str, limit: int, before: str | None
    ) -> tuple[list[MessageDTO], str | None]:
        is_member = await self.chats_client.check_membership(chat_id, user_id)
        if not is_member:
            raise AppError(ErrorCode.NOT_MEMBER)

        return await self.repo.get_history(chat_id, user_id, limit, before)

    async def edit_message(
        self, message_id: str, user_id: str, request: EditMessageRequest
    ) -> MessageDTO:
        message = await self.repo.get_by_id(message_id)
        if not message:
            raise AppError(ErrorCode.NOT_FOUND)

        self.policy.check_author(message.author_id, user_id)
        self.policy.check_edit_window(message.created_at)
        self.policy.validate_content(request.text, request.entities)

        message.text = request.text
        message.entities = request.entities
        message.edited_at = self.clock.now()

        await self.repo.save(message)

        await self.publisher.publish(
            "message.edited",
            {"message_id": message.id, "chat_id": message.chat_id},
        )

        return message

    async def delete_message(self, message_id: str, user_id: str, scope: str) -> None:
        message = await self.repo.get_by_id(message_id)
        if not message:
            raise AppError(ErrorCode.NOT_FOUND)

        self.policy.check_author(message.author_id, user_id)

        if scope == "all":
            await self.repo.mark_deleted_for_all(message_id)
            await self.publisher.publish(
                "message.deleted",
                {"message_id": message.id, "chat_id": message.chat_id},
            )
        elif scope == "me":
            await self.repo.hide_for_user(message_id, user_id)
            await self.publisher.publish(
                "message.hidden",
                {"message_id": message.id, "chat_id": message.chat_id, "user_id": user_id},
            )

    async def mark_read(self, chat_id: str, user_id: str) -> None:
        is_member = await self.chats_client.check_membership(chat_id, user_id)
        if not is_member:
            raise AppError(ErrorCode.NOT_MEMBER)

        await self.chats_client.update_last_read(chat_id, user_id)

        await self.publisher.publish(
            "message.read",
            {"chat_id": chat_id, "user_id": user_id},
        )
