from datetime import datetime
from typing import Self
from uuid import UUID

from kokogram_shared import UrlSigner
from pydantic import BaseModel, ConfigDict, Field, SecretStr, StrictStr, field_validator

from app.models import User


class RegisterRequest(BaseModel):
    username: StrictStr | None = None
    password: SecretStr | None = None
    email: StrictStr | None = None
    phone: StrictStr | None = None


class UserResponse(BaseModel):
    id: UUID
    username: str
    status: str | None
    avatar_url: str | None = None

    @classmethod
    def from_user(cls, user: User, signer: UrlSigner) -> Self:
        response = cls.model_validate(user, from_attributes=True)
        if user.avatar_key is not None:
            response.avatar_url = signer.sign(f"/api/v1/users/{user.id}/avatar")
        return response


class OwnUserResponse(UserResponse):
    email: str | None
    phone: str | None


class UsersResponse(BaseModel):
    items: list[UserResponse]


class UpdateProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: StrictStr | None = None
    status: StrictStr | None = None


class UserIdsQuery(BaseModel):
    ids: list[UUID] = Field(min_length=1, max_length=100)

    @field_validator("ids", mode="before")
    @classmethod
    def split_ids(cls, value: object) -> object:
        if isinstance(value, str):
            value = [value]
        if isinstance(value, list):
            result = []
            for item in value:
                if isinstance(item, str):
                    result.extend(part.strip() for part in item.split(","))
                else:
                    result.append(item)
            return result
        return value


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
