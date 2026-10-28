from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "validation_error"
    EMAIL_TAKEN = "email_taken"
    PHONE_TAKEN = "phone_taken"
    USERNAME_TAKEN = "username_taken"
    INVALID_CREDENTIALS = "invalid_credentials"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_MEMBER = "not_member"
    BLOCKED = "blocked"
    EDIT_WINDOW_EXPIRED = "edit_window_expired"
    NOT_A_CONTACT = "not_a_contact"
    CONTACT_LIMIT_REACHED = "contact_limit_reached"
    ALREADY_MEMBER = "already_member"
    NOT_FOUND = "not_found"
    FILE_TOO_LARGE = "file_too_large"
    GIF_UNAVAILABLE = "gif_unavailable"
    SERVICE_UNAVAILABLE = "service_unavailable"


class ValidationReason(StrEnum):
    INVALID_EMAIL = "invalid_email"
    INVALID_PHONE = "invalid_phone"
    PASSWORD_LENGTH = "password_length"
    PASSWORD_COMPOSITION = "password_composition"
    USERNAME_REQUIRED = "username_required"
    USERNAME_FORMAT = "username_format"
    USERNAME_LENGTH = "username_length"
    STATUS_LENGTH = "status_length"
    AVATAR_FORMAT = "avatar_format"
    TITLE_LENGTH = "title_length"
    TEXT_TOO_LONG = "text_too_long"
    MESSAGE_EMPTY = "message_empty"
    QUERY_TOO_LONG = "query_too_long"
    SELF_TARGET = "self_target"
    GIF_INVALID = "gif_invalid"


# HTTP-статусы по таблице HLD 4.1
HTTP_STATUS: dict[ErrorCode, int] = {
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.EMAIL_TAKEN: 409,
    ErrorCode.PHONE_TAKEN: 409,
    ErrorCode.USERNAME_TAKEN: 409,
    ErrorCode.INVALID_CREDENTIALS: 401,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.FORBIDDEN: 403,
    ErrorCode.NOT_MEMBER: 403,
    ErrorCode.BLOCKED: 403,
    ErrorCode.EDIT_WINDOW_EXPIRED: 403,
    ErrorCode.NOT_A_CONTACT: 422,
    ErrorCode.CONTACT_LIMIT_REACHED: 409,
    ErrorCode.ALREADY_MEMBER: 409,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.FILE_TOO_LARGE: 413,
    ErrorCode.GIF_UNAVAILABLE: 503,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
}

# тексты по умолчанию (для пользователя)
DEFAULT_MESSAGE: dict[ErrorCode, str] = {
    ErrorCode.VALIDATION_ERROR: "Некорректные данные",
    ErrorCode.EMAIL_TAKEN: "Этот адрес электронной почты уже зарегистрирован",
    ErrorCode.PHONE_TAKEN: "Этот номер телефона уже зарегистрирован",
    ErrorCode.USERNAME_TAKEN: "Этот username уже используется",
    ErrorCode.INVALID_CREDENTIALS: "Неверный логин или пароль",
    ErrorCode.UNAUTHORIZED: "Требуется авторизация",
    ErrorCode.FORBIDDEN: "Недостаточно прав для этого действия",
    ErrorCode.NOT_MEMBER: "Вы не являетесь участником чата",
    ErrorCode.BLOCKED: "Отправка сообщений невозможна: пользователь заблокирован",
    ErrorCode.EDIT_WINDOW_EXPIRED: "Сообщение нельзя редактировать спустя 24 часа",
    ErrorCode.NOT_A_CONTACT: "Пользователя нет в ваших контактах",
    ErrorCode.CONTACT_LIMIT_REACHED: "В списке контактов уже 50 пользователей",
    ErrorCode.ALREADY_MEMBER: "Пользователь уже состоит в чате",
    ErrorCode.NOT_FOUND: "Объект не найден",
    ErrorCode.FILE_TOO_LARGE: "Файл слишком большой",
    ErrorCode.GIF_UNAVAILABLE: "Сервис GIF временно недоступен",
    ErrorCode.SERVICE_UNAVAILABLE: "Сервис временно недоступен",
}


def error_body(
    code: ErrorCode | str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {"error": {"code": str(code), "message": message, "details": details or []}}


class AppError(Exception):

    def __init__(
        self,
        code: ErrorCode,
        message: str | None = None,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        self.code = code
        self.message = message or DEFAULT_MESSAGE[code]
        self.details = details or []
        super().__init__(f"{code}: {self.message}")

    @property
    def status_code(self) -> int:
        return HTTP_STATUS[self.code]

    def to_body(self) -> dict[str, Any]:
        return error_body(self.code, self.message, self.details)

    @classmethod
    def validation(cls, *reasons: ValidationReason, field: str | None = None) -> "AppError":
        details = [{"field": field, "reason": str(r)} for r in reasons]
        return cls(ErrorCode.VALIDATION_ERROR, details=details)
