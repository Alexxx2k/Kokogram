from datetime import datetime, timedelta

from kokogram_shared import AppError, Clock, ErrorCode, ValidationReason

from messages.app.api.schemas import EntityDTO

MAX_TEXT_LENGTH = 2000
EDIT_WINDOW_HOURS = 24


class MessagePolicy:
    def __init__(self, clock: Clock):
        self.clock = clock

    def check_edit_window(self, created_at: datetime) -> None:
        if self.clock.now() - created_at > timedelta(hours=EDIT_WINDOW_HOURS):
            raise AppError(ErrorCode.EDIT_WINDOW_EXPIRED)

    def check_author(self, sender_id: str, current_user_id: str) -> None:
        if sender_id != current_user_id:
            raise AppError(ErrorCode.FORBIDDEN)

    def validate_content(
        self,
        text: str | None,
        entities: list[EntityDTO] | None,
        has_attachment: bool = False,
    ) -> None:
        if text and len(text) > MAX_TEXT_LENGTH:
            raise AppError.validation(ValidationReason.TEXT_TOO_LONG, field="text")

        if (text is None or not text.strip()) and not has_attachment:
            raise AppError.validation(ValidationReason.MESSAGE_EMPTY, field="text")

        if entities:
            text_length = len(text) if text else 0
            for entity in entities:
                if (
                    entity.offset < 0
                    or entity.length <= 0
                    or entity.offset + entity.length > text_length
                ):
                    raise AppError(
                        ErrorCode.VALIDATION_ERROR,
                        details=[{"field": "entities", "reason": "out_of_bounds"}],
                    )
