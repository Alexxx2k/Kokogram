from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from kokogram_shared import UrlSigner

from app.api.dependencies import (
    get_avatar_service,
    get_current_user,
    get_settings,
    get_url_signer,
)
from app.api.schemas import OwnUserResponse
from app.config import Settings
from app.models import User
from app.services.avatars import AvatarService

router = APIRouter(prefix="/users", tags=["avatars"])


@router.put("/me/avatar", response_model=OwnUserResponse)
async def upload_avatar(
    file: Annotated[UploadFile, File()],
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AvatarService, Depends(get_avatar_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    signer: Annotated[UrlSigner, Depends(get_url_signer)],
) -> OwnUserResponse:
    try:
        data = await file.read(settings.avatar_max_bytes + 1)
    finally:
        await file.close()
    return OwnUserResponse.from_user(await service.replace(user.id, data), signer)


@router.get("/{user_id}/avatar")
async def download_avatar(
    user_id: UUID,
    service: Annotated[AvatarService, Depends(get_avatar_service)],
    expires: Annotated[str | None, Query()] = None,
    sig: Annotated[str | None, Query()] = None,
) -> Response:
    avatar = await service.download(user_id, expires, sig)
    return Response(
        content=avatar.data,
        media_type=avatar.content_type,
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )
