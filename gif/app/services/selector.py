from dataclasses import dataclass
from typing import List, Optional

MAX_SEND_SIZE = 50 * 1024 * 1024
MAX_PREVIEW_SIZE = 1 * 1024 * 1024


@dataclass
class GifVariant:
    url: str
    size: int


@dataclass
class SelectedGif:
    send_url: str
    preview_url: str


class GifVariantSelector:
    def select(self, variants: List[GifVariant]) -> Optional[SelectedGif]:
        valid_send_variants = [v for v in variants if v.size <= MAX_SEND_SIZE]
        if not valid_send_variants:
            return None

        send_variant = sorted(valid_send_variants, key=lambda v: v.size, reverse=True)[0]

        valid_preview_variants = [v for v in variants if v.size <= MAX_PREVIEW_SIZE]
        if not valid_preview_variants:
            return None

        preview_variant = sorted(valid_preview_variants, key=lambda v: v.size, reverse=True)[0]

        return SelectedGif(send_url=send_variant.url, preview_url=preview_variant.url)
