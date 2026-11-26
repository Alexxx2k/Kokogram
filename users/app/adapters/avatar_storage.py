import asyncio

import boto3
from botocore import UNSIGNED
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from kokogram_shared import AppError, ErrorCode

from app.config import Settings
from app.ports.avatar_storage import AvatarFile


class S3AvatarStorage:
    def __init__(self, settings: Settings) -> None:
        if bool(settings.s3_access_key) != bool(settings.s3_secret_key):
            raise ValueError("S3_ACCESS_KEY и S3_SECRET_KEY задаются вместе")
        self._bucket = settings.s3_bucket
        self._max_bytes = settings.avatar_max_bytes
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key or None,
            aws_secret_access_key=settings.s3_secret_key or None,
            config=Config(
                signature_version="s3v4" if settings.s3_access_key else UNSIGNED,
                s3={"addressing_style": "path"},
                connect_timeout=5,
                read_timeout=15,
                retries={"max_attempts": 2, "mode": "standard"},
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )

    async def put(self, key: str, avatar: AvatarFile) -> None:
        try:
            await asyncio.to_thread(
                self._client.put_object,
                Bucket=self._bucket,
                Key=key,
                Body=avatar.data,
                ContentType=avatar.content_type,
            )
        except (BotoCoreError, ClientError) as exc:
            raise AppError(ErrorCode.SERVICE_UNAVAILABLE) from exc

    async def get(self, key: str) -> AvatarFile:
        try:
            return await asyncio.to_thread(self._get, key)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in {"NoSuchKey", "NotFound", "404"}:
                raise AppError(ErrorCode.NOT_FOUND) from exc
            raise AppError(ErrorCode.SERVICE_UNAVAILABLE) from exc
        except BotoCoreError as exc:
            raise AppError(ErrorCode.SERVICE_UNAVAILABLE) from exc

    def _get(self, key: str) -> AvatarFile:
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        body = response["Body"]
        try:
            data = body.read(self._max_bytes + 1)
        finally:
            body.close()
        if len(data) > self._max_bytes:
            raise AppError(ErrorCode.FILE_TOO_LARGE)
        return AvatarFile(data=data, content_type=response["ContentType"])

    async def delete(self, key: str) -> None:
        try:
            await asyncio.to_thread(self._client.delete_object, Bucket=self._bucket, Key=key)
        except (BotoCoreError, ClientError) as exc:
            raise AppError(ErrorCode.SERVICE_UNAVAILABLE) from exc

    async def close(self) -> None:
        await asyncio.to_thread(self._client.close)
