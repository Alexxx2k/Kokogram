from messages.app.ports.chats_client import ChatsClient


class MockChatsClient(ChatsClient):
    async def check_membership(self, chat_id: str, user_id: str) -> bool:
        return True

    async def update_last_read(self, chat_id: str, user_id: str) -> None:
        pass
