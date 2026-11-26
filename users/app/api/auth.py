from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from kokogram_shared import UrlSigner

from app.api.dependencies import (
    get_auth_service,
    get_bearer_token,
    get_session_service,
    get_url_signer,
)
from app.api.schemas import LoginRequest, LoginResponse, RegisterRequest, UserResponse
from app.services.auth import AuthService
from app.services.sessions import SessionService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register(
    body: RegisterRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
    signer: Annotated[UrlSigner, Depends(get_url_signer)],
) -> UserResponse:
    user = await service.register(
        username=body.username,
        password=body.password.get_secret_value() if body.password is not None else None,
        email=body.email,
        phone=body.phone,
    )
    return UserResponse.from_user(user, signer)


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
    signer: Annotated[UrlSigner, Depends(get_url_signer)],
) -> LoginResponse:
    result = await service.login(
        login=body.login,
        password=body.password.get_secret_value() if body.password is not None else None,
    )
    return LoginResponse(
        token=result.session.token,
        expires_at=result.session.expires_at,
        user=UserResponse.from_user(result.user, signer),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    token: Annotated[str, Depends(get_bearer_token)],
    service: Annotated[SessionService, Depends(get_session_service)],
) -> Response:
    await service.logout(token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
