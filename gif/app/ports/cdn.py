from typing import Protocol

class CdnClient(Protocol):
    async def get_content_length(self, url: str) -> int | None: ...
