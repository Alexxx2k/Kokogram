from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user, get_profile_service
from app.api.schemas import OwnUserResponse, UpdateProfileRequest, UserResponse, UsersResponse
from app.models import User
from app.services.profile import ProfileService

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(get_current_user)])


# Статический /me должен быть объявлен раньше динамического /{user_id}.
@router.get("/me", response_model=OwnUserResponse)
async def get_own_profile(
    user: Annotated[User, Depends(get_current_user)],
) -> OwnUserResponse:
    return OwnUserResponse.from_user(user)


@router.patch("/me", response_model=OwnUserResponse)
async def update_own_profile(
    body: UpdateProfileRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> OwnUserResponse:
    updated = await service.update(user.id, body.model_dump(exclude_unset=True))
    return OwnUserResponse.from_user(updated)


@router.get("", response_model=UsersResponse)
async def search_users(
    username: Annotated[str, Query()],
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> UsersResponse:
    users = await service.search(username)
    return UsersResponse(items=[UserResponse.from_user(user) for user in users])


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_profile(
    user_id: UUID,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> UserResponse:
    return UserResponse.from_user(await service.get(user_id))
