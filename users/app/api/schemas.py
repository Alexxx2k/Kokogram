from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, SecretStr, StrictStr


class RegisterRequest(BaseModel):
    username: StrictStr | None = None
    password: SecretStr | None = None
    email: StrictStr | None = None
    phone: StrictStr | None = None


class UserResponse(BaseModel):
    id: UUID
    username: str
    status: str | None
    avatar_url: str | None


class LoginRequest(BaseModel):
    login: StrictStr | None = None
    password: SecretStr | None = None


class LoginResponse(BaseModel):
    token: str
    expires_at: datetime
    user: UserResponse


class VerifySessionRequest(BaseModel):
    token: SecretStr | None = None


class VerifySessionResponse(BaseModel):
    user_id: UUID
