import logging
from typing import Literal

from kokogram_shared import AppError, Clock, ErrorCode, IdGenerator

from messages.app.api.schemas import (
    EditMessageRequest,
    MessageDTO,
    ReplyToDTO,
    SendMessageRequest,
)
from messages.app.models import MembershipDTO
from messages.app.ports.chats_client import ChatsClient
from messages.app.ports.event_publisher import EventPublisher
from messages.app.ports.message_repo import MessageRepository
from messages.app.ports.users_client import UsersClient
from messages.app.services.message_policy import MessagePolicy

logger = logging.getLogger("messages")


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

    def _get_recipient_ids(self, membership: MembershipDTO, sender_id: str) -> list[str]:
        return [m.user_id for m in membership.members if m.user_id != sender_id]

    async def send_message(
        self, chat_id: str, user_id: str, request: SendMessageRequest
    ) -> MessageDTO:
        self.policy.validate_content(request.text, request.entities)

        membership = await self.chats_client.check_membership(chat_id, user_id)
        if not membership.is_member:
            logger.warning(
                "send_failed_not_member",
                extra={"chat_id": chat_id, "user_id": user_id},
            )
            raise AppError(ErrorCode.NOT_MEMBER)

        if membership.chat_type == "personal":
            peer_id = next(
                (m.user_id for m in membership.members if m.user_id != user_id),
                None,
            )
            if peer_id:
                is_blocked = await self.users_client.check_blocked(user_id, peer_id)
                if is_blocked:
                    logger.warning(
                        "send_failed_blocked",
                        extra={
                            "chat_id": chat_id,
                            "user_id": user_id,
                            "peer_id": peer_id,
                        },
                    )
                    raise AppError(ErrorCode.BLOCKED)

        if request.reply_to_id:
            original_msg = await self.repo.get_by_id(request.reply_to_id)
            if not original_msg or original_msg.chat_id != chat_id:
                logger.warning(
                    "send_failed_invalid_reply",
                    extra={"chat_id": chat_id, "reply_to_id": request.reply_to_id},
                )
                raise AppError(ErrorCode.NOT_FOUND)

        message = MessageDTO(
            id=str(self.id_generator.new_id()),
            chat_id=chat_id,
            sender_id=user_id,
            text=request.text,
            entities=request.entities or [],
            created_at=self.clock.now(),
            edited_at=None,
            status="sent",
            is_reply=bool(request.reply_to_id),
            reply_to_id=request.reply_to_id,
        )

        await self.repo.save(message)

        logger.info(
            "message_created",
            extra={"message_id": message.id, "chat_id": chat_id, "sender_id": user_id},
        )

        recipient_ids = self._get_recipient_ids(membership, user_id)
        await self.publisher.publish(
            "message.created",
            {
                "message": message.model_dump(mode="json"),
                "recipient_ids": recipient_ids,
            },
        )

        return await self._attach_reply_info(message)

    async def get_history(
        self, chat_id: str, user_id: str, limit: int, before: str | None
    ) -> tuple[list[MessageDTO], str | None]:
        membership = await self.chats_client.check_membership(chat_id, user_id)
        if not membership.is_member:
            logger.warning(
                "history_failed_not_member",
                extra={"chat_id": chat_id, "user_id": user_id},
            )
            raise AppError(ErrorCode.NOT_MEMBER)

        messages, next_cursor = await self.repo.get_history(chat_id, user_id, limit, before)

        for msg in messages:
            await self._populate_reply_to(msg)
            await self._populate_status(msg, user_id, membership)

        return messages, next_cursor

    async def edit_message(
        self, message_id: str, user_id: str, request: EditMessageRequest
    ) -> MessageDTO:
        message = await self.repo.get_by_id(message_id)
        if not message:
            raise AppError(ErrorCode.NOT_FOUND)

        try:
            self.policy.check_author(message.sender_id, user_id)
            self.policy.check_edit_window(message.created_at)
        except AppError as e:
            logger.warning(
                "edit_failed",
                extra={"message_id": message_id, "user_id": user_id, "error": str(e)},
            )
            raise

        self.policy.validate_content(request.text, request.entities)

        updated_message = message.model_copy(
            update={
                "text": request.text,
                "entities": request.entities or [],
                "edited_at": self.clock.now(),
            }
        )

        await self.repo.save(updated_message)

        logger.info(
            "message_edited",
            extra={"message_id": message_id, "user_id": user_id},
        )

        membership = await self.chats_client.check_membership(message.chat_id, user_id)
        recipient_ids = self._get_recipient_ids(membership, user_id)

        await self.publisher.publish(
            "message.edited",
            {
                "message": updated_message.model_dump(mode="json"),
                "recipient_ids": recipient_ids,
            },
        )

        return await self._attach_reply_info(updated_message)

    async def delete_message(
        self, message_id: str, user_id: str, scope: Literal["all", "me"]
    ) -> None:
        message = await self.repo.get_by_id(message_id)
        if not message:
            raise AppError(ErrorCode.NOT_FOUND)

        try:
            self.policy.check_author(message.sender_id, user_id)
        except AppError:
            logger.warning(
                "delete_failed_forbidden",
                extra={"message_id": message_id, "user_id": user_id},
            )
            raise

        if scope == "all":
            await self.repo.mark_deleted_for_all(message_id)

            logger.info(
                "message_deleted_for_all",
                extra={"message_id": message_id, "user_id": user_id},
            )

            membership = await self.chats_client.check_membership(message.chat_id, user_id)
            recipient_ids = self._get_recipient_ids(membership, user_id)

            await self.publisher.publish(
                "message.deleted",
                {
                    "chat_id": message.chat_id,
                    "message_id": message.id,
                    "recipient_ids": recipient_ids,
                },
            )
        elif scope == "me":
            await self.repo.hide_for_user(message_id, user_id)
            logger.info(
                "message_hidden_for_user",
                extra={"message_id": message_id, "user_id": user_id},
            )
        else:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                details=[{"field": "scope", "reason": "invalid_scope"}],
            )

    async def mark_read(self, chat_id: str, user_id: str) -> None:
        membership = await self.chats_client.check_membership(chat_id, user_id)
        if not membership.is_member:
            logger.warning(
                "read_failed_not_member",
                extra={"chat_id": chat_id, "user_id": user_id},
            )
            raise AppError(ErrorCode.NOT_MEMBER)

        last_read_at = self.clock.now()
        await self.chats_client.update_last_read(chat_id, user_id, last_read_at)

        logger.info(
            "messages_read",
            extra={"chat_id": chat_id, "user_id": user_id},
        )

        recipient_ids = self._get_recipient_ids(membership, user_id)

        await self.publisher.publish(
            "message.read",
            {
                "chat_id": chat_id,
                "reader_id": user_id,
                "last_read_at": last_read_at.isoformat(),
                "recipient_ids": recipient_ids,
            },
        )

    async def _populate_reply_to(self, message: MessageDTO) -> None:
        if not message.is_reply or not message.reply_to_id:
            return

        original_msg = await self.repo.get_by_id(message.reply_to_id)
        if not original_msg:
            logger.info(
                "reply_to_deleted_message",
                extra={"message_id": message.id, "reply_to_id": message.reply_to_id},
            )
            message.reply_to = ReplyToDTO(deleted=True)
        else:
            text_preview = original_msg.text
            if text_preview and len(text_preview) > 50:
                text_preview = text_preview[:50] + "..."

            message.reply_to = ReplyToDTO(
                message_id=original_msg.id,
                sender_id=original_msg.sender_id,
                text_preview=text_preview,
                deleted=False,
            )

    async def _attach_reply_info(self, message: MessageDTO) -> MessageDTO:
        await self._populate_reply_to(message)
        return message

    async def _populate_status(
        self, message: MessageDTO, current_user_id: str, membership: MembershipDTO
    ) -> None:
        if message.sender_id != current_user_id:
            message.status = None
            return

        max_other_read = None
        for member in membership.members:
            if member.user_id != message.sender_id and member.last_read_at:
                if max_other_read is None or member.last_read_at > max_other_read:
                    max_other_read = member.last_read_at

        if max_other_read and max_other_read >= message.created_at:
            message.status = "read"
        else:
            message.status = "sent"
