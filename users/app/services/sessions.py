import hashlib
from datetime import timedelta
from uuid import UUID

from kokogram_shared import AppError, Clock, ErrorCode, IdGenerator, TokenGenerator

from app.models import Session, SessionToken
from app.ports.session_repository import SessionRepository


class SessionService:
    def __init__(
        self,
        sessions: SessionRepository,
        clock: Clock,
        id_generator: IdGenerator,
        token_generator: TokenGenerator,
        ttl: timedelta = timedelta(days=30),
    ) -> None:
        if not timedelta(0) < ttl <= timedelta(days=30):
            raise ValueError("Срок сессии должен быть положительным и не больше 30 суток")
        self._sessions = sessions
        self._clock = clock
        self._id_generator = id_generator
        self._token_generator = token_generator
        self._ttl = ttl

    async def create(self, user_id: UUID) -> SessionToken:
        token = self._token_generator.new_token()
        now = self._clock.now()
        session = Session(
            id=self._id_generator.new_id(),
            user_id=user_id,
            token_hash=self._hash_token(token),
            created_at=now,
            expires_at=now + self._ttl,
        )
        await self._sessions.add(session)
        return SessionToken(token=token, expires_at=session.expires_at)

    async def verify(self, token: str | None) -> UUID:
        if not token:
            raise AppError(ErrorCode.UNAUTHORIZED)
        session = await self._sessions.get_by_token_hash(self._hash_token(token))
        if session is None or self._clock.now() >= session.expires_at:
            raise AppError(ErrorCode.UNAUTHORIZED)
        return session.user_id

    async def logout(self, token: str) -> None:
        await self.verify(token)
        await self._sessions.delete_by_token_hash(self._hash_token(token))

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
