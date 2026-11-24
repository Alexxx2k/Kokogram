import asyncio

import bcrypt


class BcryptPasswordHasher:
    async def hash(self, password: str) -> str:
        return await asyncio.to_thread(self._hash, password)

    @staticmethod
    def _hash(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=10)).decode("ascii")

    async def verify(self, password: str, password_hash: str) -> bool:
        return await asyncio.to_thread(self._verify, password, password_hash)

    @staticmethod
    def _verify(password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
        except (ValueError, UnicodeError):
            return False
