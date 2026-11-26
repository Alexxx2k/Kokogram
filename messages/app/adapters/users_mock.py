class MockUsersClient:
    def __init__(self):
        self._blocks: set[tuple[str, str]] = set()

    async def check_blocked(self, user_a: str, user_b: str) -> bool:
        return (user_a, user_b) in self._blocks or (user_b, user_a) in self._blocks

    def block_user(self, user_a: str, user_b: str) -> None:
        self._blocks.add((user_a, user_b))
