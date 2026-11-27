from typing import Annotated

from fastapi import APIRouter, Depends, Query
from kokogram_shared import UrlSigner

from app.api.dependencies import get_profile_service, get_session_service, get_url_signer
from app.api.schemas import (
    UserIdsQuery,
    UserResponse,
    UsersResponse,
    VerifySessionRequest,
    VerifySessionResponse,
)
from app.services.profile import ProfileService
from app.services.sessions import SessionService

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/sessions/verify", response_model=VerifySessionResponse)
async def verify_session(
    body: VerifySessionRequest,
    service: Annotated[SessionService, Depends(get_session_service)],
) -> VerifySessionResponse:
    token = body.token.get_secret_value() if body.token is not None else None
    return VerifySessionResponse(user_id=await service.verify(token))


@router.get("/users", response_model=UsersResponse)
async def get_users(
    query: Annotated[UserIdsQuery, Query()],
    service: Annotated[ProfileService, Depends(get_profile_service)],
    signer: Annotated[UrlSigner, Depends(get_url_signer)],
) -> UsersResponse:
    users = await service.get_many(query.ids)
    return UsersResponse(items=[UserResponse.from_user(user, signer) for user in users])
