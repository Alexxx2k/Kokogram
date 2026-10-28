from typing import Protocol
from uuid import UUID, uuid4


class IdGenerator(Protocol):

    def new_id(self) -> UUID: ...


class UuidGenerator:

    def new_id(self) -> UUID:
        return uuid4()


class SequentialIdGenerator:

    def __init__(self, start: int = 1) -> None:
        self._next = start

    def new_id(self) -> UUID:
        value = UUID(int=self._next)
        self._next += 1
        return value
