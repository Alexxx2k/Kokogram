import asyncio
import warnings
from io import BytesIO

from kokogram_shared import AppError, ValidationReason
from PIL import Image, UnidentifiedImageError


class PillowAvatarInspector:
    async def content_type(self, data: bytes) -> str:
        return await asyncio.to_thread(self._inspect, data)

    @staticmethod
    def _inspect(data: bytes) -> str:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(BytesIO(data), formats=["JPEG", "PNG"]) as image:
                    image_format = image.format
                    image.verify()
                with Image.open(BytesIO(data), formats=["JPEG", "PNG"]) as image:
                    image.load()
            return "image/jpeg" if image_format == "JPEG" else "image/png"
        except (
            UnidentifiedImageError,
            OSError,
            ValueError,
            SyntaxError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ) as exc:
            raise AppError.validation(ValidationReason.AVATAR_FORMAT, field="file") from exc
