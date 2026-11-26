import re

from email_validator import EmailNotValidError, validate_email
from kokogram_shared import AppError, ErrorCode, ValidationReason


def validate_username(value: str | None) -> str:
    if not value:
        raise AppError.validation(ValidationReason.USERNAME_REQUIRED, field="username")
    if not 3 <= len(value) <= 12:
        raise AppError.validation(ValidationReason.USERNAME_LENGTH, field="username")
    if re.fullmatch(r"[A-Za-z0-9_]+", value) is None:
        raise AppError.validation(ValidationReason.USERNAME_FORMAT, field="username")
    return value


def validate_password(value: str | None) -> str:
    if value is None or not 6 <= len(value) <= 12:
        raise AppError.validation(ValidationReason.PASSWORD_LENGTH, field="password")
    if not any(char.isalpha() for char in value) or not any(char.isdecimal() for char in value):
        raise AppError.validation(ValidationReason.PASSWORD_COMPOSITION, field="password")
    return value


def validate_status(value: str | None) -> str | None:
    if value is not None and len(value) > 20:
        raise AppError.validation(ValidationReason.STATUS_LENGTH, field="status")
    return value


def normalize_email(value: str) -> str:
    try:
        normalized = validate_email(value.strip(), check_deliverability=False).normalized.lower()
    except EmailNotValidError as exc:
        raise AppError.validation(ValidationReason.INVALID_EMAIL, field="email") from exc
    if len(normalized) > 254:
        raise AppError.validation(ValidationReason.INVALID_EMAIL, field="email")
    return normalized


def normalize_phone(value: str) -> str:
    normalized = re.sub(r"[ ()-]", "", value.strip())
    if re.fullmatch(r"(?:\+7|7|8)[0-9]{10}", normalized) is None:
        raise AppError.validation(ValidationReason.INVALID_PHONE, field="phone")
    return "+7" + normalized[-10:]


def normalize_contacts(email: str | None, phone: str | None) -> tuple[str | None, str | None]:
    if email is None and phone is None:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            message="Укажите email или телефон",
            details=[
                {"field": "email", "reason": str(ValidationReason.INVALID_EMAIL)},
                {"field": "phone", "reason": str(ValidationReason.INVALID_PHONE)},
            ],
        )
    return (
        normalize_email(email) if email is not None else None,
        normalize_phone(phone) if phone is not None else None,
    )
