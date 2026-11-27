from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AvatarFile:
    data: bytes
    content_type: str


class AvatarStorage(Protocol):
    async def put(self, key: str, avatar: AvatarFile) -> None: ...

    async def get(self, key: str) -> AvatarFile: ...

    async def delete(self, key: str) -> None: ...


class AvatarInspector(Protocol):
    async def content_type(self, data: bytes) -> str: ...
