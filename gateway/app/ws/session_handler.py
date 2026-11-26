import json
import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from kokogram_shared.errors import AppError, ErrorCode

from gateway.app.ports.presence_client import PresenceClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WsAction:
    response: dict[str, Any] | None = None
    should_close: bool = False
    close_code: int = 1000


def _error_message(code: ErrorCode | str, message: str) -> dict[str, Any]:
    return {
        "type": "error",
        "payload": {
            "code": str(code),
            "message": message,
        },
    }


def _parse_user_ids(payload: dict[str, Any]) -> list[str] | None:
    if "user_ids" not in payload:
        return None
    raw_ids = payload["user_ids"]
    if not isinstance(raw_ids, list):
        return None

    normalized: list[str] = []
    seen: set[str] = set()
    for item in raw_ids:
        if not isinstance(item, str):
            return None
        try:
            parsed = str(UUID(item))
        except ValueError:
            return None
        if parsed not in seen:
            seen.add(parsed)
            normalized.append(parsed)
    return normalized


class WsSessionHandler:
    def __init__(self, presence_client: PresenceClient) -> None:
        self._presence_client = presence_client

    async def handle_raw_message(self, connection_id: str, raw_text: str) -> WsAction:
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            return WsAction(
                response=_error_message(ErrorCode.VALIDATION_ERROR, "Некорректный JSON"),
            )

        if not isinstance(data, dict):
            return WsAction(
                response=_error_message(
                    ErrorCode.VALIDATION_ERROR,
                    "Сообщение должно быть JSON-объектом",
                ),
            )

        msg_type = data.get("type")
        if not isinstance(msg_type, str) or not msg_type:
            return WsAction(
                response=_error_message(
                    ErrorCode.VALIDATION_ERROR,
                    "Поле type должно быть непустой строкой",
                ),
            )

        if "payload" in data:
            payload = data["payload"]
            if not isinstance(payload, dict):
                return WsAction(
                    response=_error_message(
                        ErrorCode.VALIDATION_ERROR,
                        "Поле payload должно быть объектом",
                    ),
                )
        elif msg_type == "ping":
            payload = {}
        else:
            return WsAction(
                response=_error_message(
                    ErrorCode.VALIDATION_ERROR,
                    "Поле payload обязательно",
                ),
            )

        try:
            return await self._dispatch(connection_id, msg_type, payload)
        except AppError as exc:
            logger.warning(
                "Ошибка обработки WS-сообщения %s для соединения %s: %s",
                msg_type,
                connection_id,
                exc,
                extra={"error_code": str(exc.code)},
            )
            if exc.code == ErrorCode.NOT_FOUND:
                return WsAction(
                    response=_error_message(exc.code, exc.message),
                    should_close=True,
                    close_code=4404,
                )
            return WsAction(
                response=_error_message(exc.code, exc.message),
                should_close=False,
            )

    async def _dispatch(
        self,
        connection_id: str,
        msg_type: str,
        payload: dict[str, Any],
    ) -> WsAction:
        if msg_type == "ping":
            await self._presence_client.ping(connection_id)
            return WsAction(response={"type": "pong", "payload": {}})

        if msg_type == "subscribe_status":
            user_ids = _parse_user_ids(payload)
            if user_ids is None:
                return WsAction(
                    response=_error_message(
                        ErrorCode.VALIDATION_ERROR,
                        "Поле user_ids должно быть списком корректных UUID",
                    ),
                )
            statuses = await self._presence_client.update_subscriptions(
                connection_id=connection_id,
                add=user_ids,
                remove=[],
            )
            return WsAction(
                response={
                    "type": "status_snapshot",
                    "payload": {
                        "statuses": [status.to_dict() for status in statuses],
                    },
                },
            )

        if msg_type == "unsubscribe_status":
            user_ids = _parse_user_ids(payload)
            if user_ids is None:
                return WsAction(
                    response=_error_message(
                        ErrorCode.VALIDATION_ERROR,
                        "Поле user_ids должно быть списком корректных UUID",
                    ),
                )
            await self._presence_client.update_subscriptions(
                connection_id=connection_id,
                add=[],
                remove=user_ids,
            )
            return WsAction(response=None)

        return WsAction(
            response=_error_message(
                ErrorCode.VALIDATION_ERROR,
                f"Неизвестный тип сообщения: {msg_type}",
            ),
        )
