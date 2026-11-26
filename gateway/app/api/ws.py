import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from kokogram_shared.errors import AppError, ErrorCode
from kokogram_shared.fastapi_middleware import REQUEST_ID_HEADER
from kokogram_shared.ids import IdGenerator
from kokogram_shared.logging import (
    reset_request_id,
    reset_user_id,
    set_request_id,
    set_user_id,
)

from gateway.app.api.dependencies import (
    get_connection_registry,
    get_id_generator,
    get_presence_client,
    get_users_client,
    get_ws_session_handler,
)
from gateway.app.ports.presence_client import PresenceClient
from gateway.app.ports.users_client import UsersClient
from gateway.app.ws.connection_registry import ConnectionRegistry
from gateway.app.ws.session_handler import WsSessionHandler

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

WS_CLOSE_UNAUTHORIZED = 4401
WS_CLOSE_INTERNAL_ERROR = 1011


async def _safe_accept(websocket: WebSocket) -> bool:
    try:
        await websocket.accept()
        return True
    except (WebSocketDisconnect, RuntimeError) as exc:
        logger.info("WS-соединение оборвалось при handshake (accept): %s", exc)
        return False


async def _safe_close(websocket: WebSocket, code: int) -> None:
    try:
        await websocket.close(code=code)
    except (WebSocketDisconnect, RuntimeError) as exc:
        logger.debug("Не удалось отправить close(%s) в WS: %s", code, exc)


async def _safe_accept_and_close(websocket: WebSocket, code: int) -> None:
    if await _safe_accept(websocket):
        await _safe_close(websocket, code=code)


async def _best_effort_disconnect(presence_client: PresenceClient, connection_id: str) -> None:
    try:
        await presence_client.disconnect(connection_id)
    except Exception as exc:
        error_code = str(exc.code) if isinstance(exc, AppError) else None
        logger.warning(
            "Не удалось уведомить presence об отключении %s: %s",
            connection_id,
            exc,
            extra={"error_code": error_code},
        )


@router.websocket("/api/v1/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    users_client: Annotated[UsersClient, Depends(get_users_client)],
    presence_client: Annotated[PresenceClient, Depends(get_presence_client)],
    registry: Annotated[ConnectionRegistry, Depends(get_connection_registry)],
    session_handler: Annotated[WsSessionHandler, Depends(get_ws_session_handler)],
    id_generator: Annotated[IdGenerator, Depends(get_id_generator)],
    token: str | None = Query(default=None),
) -> None:
    current_task = asyncio.current_task()
    if current_task is not None:
        registry.track_task(current_task)

    request_id = websocket.headers.get(REQUEST_ID_HEADER) or str(id_generator.new_id())
    req_token = set_request_id(request_id)
    user_token = set_user_id(None)

    try:
        clean_token = (token or "").strip()
        if not clean_token:
            await _safe_accept_and_close(websocket, code=WS_CLOSE_UNAUTHORIZED)
            return

        try:
            user_id = await users_client.verify_session(clean_token)
        except Exception as exc:
            error_code = str(exc.code) if isinstance(exc, AppError) else None
            logger.warning(
                "Не удалось проверить токен WebSocket-соединения: %s",
                exc,
                extra={"error_code": error_code},
            )
            await _safe_accept_and_close(websocket, code=WS_CLOSE_INTERNAL_ERROR)
            return

        if not user_id:
            await _safe_accept_and_close(websocket, code=WS_CLOSE_UNAUTHORIZED)
            return

        uid = str(user_id)
        set_user_id(uid)
        if not await _safe_accept(websocket):
            return

        connection_id = str(id_generator.new_id())
        registry.register(connection_id, websocket, user_id=uid)

        try:
            await presence_client.register_connection(
                connection_id=connection_id,
                user_id=uid,
            )
        except Exception as exc:
            registry.unregister(connection_id)
            error_code = str(exc.code) if isinstance(exc, AppError) else None
            logger.warning(
                "Не удалось зарегистрировать WS-соединение %s в presence: %s",
                connection_id,
                exc,
                extra={"error_code": error_code},
            )
            await _best_effort_disconnect(presence_client, connection_id)
            await _safe_close(websocket, code=WS_CLOSE_INTERNAL_ERROR)
            return

        logger.info("WS-соединение %s установлено", connection_id)

        try:
            while True:
                message = await websocket.receive()
                if message["type"] == "websocket.disconnect":
                    break

                raw_text = message.get("text")
                if raw_text is None:
                    sent = await registry.send(
                        connection_id,
                        {
                            "type": "error",
                            "payload": {
                                "code": str(ErrorCode.VALIDATION_ERROR),
                                "message": "Ожидается текстовое JSON-сообщение",
                            },
                        },
                    )
                    if not sent:
                        break
                    continue

                action = await session_handler.handle_raw_message(connection_id, raw_text)
                if action.response is not None:
                    sent = await registry.send(connection_id, action.response)
                    if not sent:
                        break
                if action.should_close:
                    await _safe_close(websocket, code=action.close_code)
                    break
        except WebSocketDisconnect:
            logger.info("WS-соединение %s закрыто клиентом", connection_id)
        except asyncio.CancelledError:
            logger.info("WS-соединение %s отменено при остановке сервера", connection_id)
            raise
        except Exception as exc:
            logger.warning("Ошибка в WS-соединении %s: %s", connection_id, exc)
        finally:
            registry.unregister(connection_id)
            await _best_effort_disconnect(presence_client, connection_id)
            logger.info("WS-соединение %s завершено", connection_id)
    finally:
        reset_user_id(user_token)
        reset_request_id(req_token)
