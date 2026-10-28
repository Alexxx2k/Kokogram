import secrets
from collections.abc import Iterable
from typing import Protocol


class TokenGenerator(Protocol):

    def new_token(self) -> str: ...


class SecretsTokenGenerator:

    def new_token(self) -> str:
        return secrets.token_urlsafe(32)


class FixedTokenGenerator:

    def __init__(self, tokens: Iterable[str] = ()) -> None:
        self._queue = list(tokens)
        self._counter = 0

    def new_token(self) -> str:
        if self._queue:
            return self._queue.pop(0)
        self._counter += 1
        return f"token-{self._counter}"
