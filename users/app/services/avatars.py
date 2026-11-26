import re
from functools import partial
from uuid import UUID

from kokogram_shared import AppError, ErrorCode, IdGenerator, UrlSigner

from app.models import User
from app.ports.avatar_storage import AvatarFile, AvatarInspector, AvatarStorage
from app.ports.transaction_hooks import TransactionHooks
from app.ports.user_repository import UserRepository


class AvatarService:
    def __init__(
        self,
        users: UserRepository,
        storage: AvatarStorage,
        inspector: AvatarInspector,
        id_generator: IdGenerator,
        signer: UrlSigner,
        hooks: TransactionHooks,
        max_bytes: int,
    ) -> None:
        self._users = users
        self._storage = storage
        self._inspector = inspector
        self._id_generator = id_generator
        self._signer = signer
        self._hooks = hooks
        self._max_bytes = max_bytes

    async def replace(self, user_id: UUID, data: bytes) -> User:
        if len(data) > self._max_bytes:
            raise AppError(ErrorCode.FILE_TOO_LARGE)
        content_type = await self._inspector.content_type(data)
        user = await self._users.get_by_id_for_update(user_id)
        if user is None:
            raise AppError(ErrorCode.NOT_FOUND)
        key = f"avatars/users/{user_id}/{self._id_generator.new_id()}"
        self._hooks.after_rollback(partial(self._storage.delete, key))
        await self._storage.put(key, AvatarFile(data=data, content_type=content_type))
        updated = await self._users.update_avatar(user_id, key)
        if updated is None:
            raise AppError(ErrorCode.NOT_FOUND)
        if user.avatar_key:
            self._hooks.after_commit(partial(self._storage.delete, user.avatar_key))
        return updated

    async def download(self, user_id: UUID, expires: str | None, sig: str | None) -> AvatarFile:
        if expires is None or sig is None or re.fullmatch(r"[0-9a-fA-F]{64}", sig) is None:
            raise AppError(ErrorCode.UNAUTHORIZED)
        self._signer.verify(f"/users/{user_id}/avatar", expires=expires, sig=sig)
        user = await self._users.get_by_id(user_id)
        if user is None or user.avatar_key is None:
            raise AppError(ErrorCode.NOT_FOUND)
        return await self._storage.get(user.avatar_key)
