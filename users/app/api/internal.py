from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_session_service
from app.api.schemas import VerifySessionRequest, VerifySessionResponse
from app.services.sessions import SessionService

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/sessions/verify", response_model=VerifySessionResponse)
async def verify_session(
    body: VerifySessionRequest,
    service: Annotated[SessionService, Depends(get_session_service)],
) -> VerifySessionResponse:
    token = body.token.get_secret_value() if body.token is not None else None
    return VerifySessionResponse(user_id=await service.verify(token))
