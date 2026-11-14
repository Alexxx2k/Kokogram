import contextvars
import json
import logging
import sys
from typing import Any

from kokogram_shared.clock import Clock, SystemClock

_request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)
_user_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("user_id", default=None)
_event_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("event_id", default=None)


def get_request_id() -> str | None:
    return _request_id_var.get()


def set_request_id(value: str | None) -> contextvars.Token[str | None]:
    return _request_id_var.set(value)


def reset_request_id(token: contextvars.Token[str | None]) -> None:
    _request_id_var.reset(token)


def get_user_id() -> str | None:
    return _user_id_var.get()


def set_user_id(value: str | None) -> contextvars.Token[str | None]:
    return _user_id_var.set(value)


def reset_user_id(token: contextvars.Token[str | None]) -> None:
    _user_id_var.reset(token)


def get_event_id() -> str | None:
    return _event_id_var.get()


def set_event_id(value: str | None) -> contextvars.Token[str | None]:
    return _event_id_var.set(value)


def reset_event_id(token: contextvars.Token[str | None]) -> None:
    _event_id_var.reset(token)


class JsonFormatter(logging.Formatter):
    def __init__(self, service: str, clock: Clock | None = None) -> None:
        super().__init__()
        self._service = service
        self._clock = clock or SystemClock()

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "time": self._clock.now().isoformat(),
            "service": self._service,
            "level": record.levelname,
            "event": record.getMessage(),
            "request_id": getattr(record, "request_id", None) or _request_id_var.get(),
            "user_id": getattr(record, "user_id", None) or _user_id_var.get(),
            "event_id": getattr(record, "event_id", None) or _event_id_var.get(),
            "error_code": getattr(record, "error_code", None),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(
    service: str,
    level: int | str = logging.INFO,
    clock: Clock | None = None,
) -> logging.Logger:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(service=service, clock=clock))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    return logging.getLogger(service)
