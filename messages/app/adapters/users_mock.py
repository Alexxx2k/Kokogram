from messages.app.ports.users_client import UsersClient


class MockUsersClient(UsersClient):
    async def check_blocked(self, user_a: str, user_b: str) -> bool:
        return False
