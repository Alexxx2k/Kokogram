class InMemoryUsersClient:
    def __init__(self, sessions: dict[str, str] | None = None) -> None:
        self._sessions: dict[str, str] = dict(sessions or {})

    def add_session(self, token: str, user_id: str) -> None:
        self._sessions[token] = str(user_id)

    def remove_session(self, token: str) -> None:
        self._sessions.pop(token, None)

    def clear(self) -> None:
        self._sessions.clear()

    async def verify_session(self, token: str) -> str | None:
        return self._sessions.get(token)
