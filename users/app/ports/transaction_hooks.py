from collections.abc import Awaitable, Callable
from typing import Protocol

Cleanup = Callable[[], Awaitable[None]]


class TransactionHooks(Protocol):
    def after_commit(self, callback: Cleanup) -> None: ...

    def after_rollback(self, callback: Cleanup) -> None: ...
