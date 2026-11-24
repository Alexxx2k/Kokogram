from kokogram_shared import AppError, Clock, ErrorCode, IdGenerator

from app.models import LoginResult, User
from app.ports.password_hasher import PasswordHasher
from app.ports.user_repository import UserRepository
from app.services.sessions import SessionService
from app.validators import (
    normalize_contacts,
    normalize_email,
    normalize_phone,
    validate_password,
    validate_username,
)


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        password_hasher: PasswordHasher,
        clock: Clock,
        id_generator: IdGenerator,
        sessions: SessionService,
    ) -> None:
        self._users = users
        self._password_hasher = password_hasher
        self._clock = clock
        self._id_generator = id_generator
        self._sessions = sessions

    async def login(self, login: str | None, password: str | None) -> LoginResult:
        if not login or not password:
            raise AppError(ErrorCode.INVALID_CREDENTIALS)
        try:
            normalized = normalize_email(login) if "@" in login else normalize_phone(login)
        except AppError as exc:
            raise AppError(ErrorCode.INVALID_CREDENTIALS) from exc
        user = (
            await self._users.get_by_email(normalized)
            if "@" in login
            else await self._users.get_by_phone(normalized)
        )
        if user is None or not await self._password_hasher.verify(password, user.password_hash):
            raise AppError(ErrorCode.INVALID_CREDENTIALS)
        session = await self._sessions.create(user.id)
        return LoginResult(user=user, session=session)

    async def register(
        self,
        *,
        username: str | None,
        password: str | None,
        email: str | None = None,
        phone: str | None = None,
    ) -> User:
        username = validate_username(username)
        password = validate_password(password)
        email, phone = normalize_contacts(email, phone)
        password_hash = await self._password_hasher.hash(password)
        user = User(
            id=self._id_generator.new_id(),
            email=email,
            phone=phone,
            password_hash=password_hash,
            username=username,
            status=None,
            avatar_key=None,
            created_at=self._clock.now(),
        )
        # Уникальность обеспечивает БД, включая одновременные регистрации.
        return await self._users.add(user)
