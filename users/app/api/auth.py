from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_auth_service
from app.api.schemas import RegisterRequest, UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register(
    body: RegisterRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    user = await service.register(
        username=body.username,
        password=body.password.get_secret_value() if body.password is not None else None,
        email=body.email,
        phone=body.phone,
    )
    return UserResponse(id=user.id, username=user.username, status=user.status, avatar_url=None)
