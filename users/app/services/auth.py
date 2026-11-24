from kokogram_shared import Clock, IdGenerator

from app.models import User
from app.ports.password_hasher import PasswordHasher
from app.ports.user_repository import UserRepository
from app.validators import normalize_contacts, validate_password, validate_username


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        password_hasher: PasswordHasher,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._users = users
        self._password_hasher = password_hasher
        self._clock = clock
        self._id_generator = id_generator

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
