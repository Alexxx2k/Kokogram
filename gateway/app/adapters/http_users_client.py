import httpx
from kokogram_shared.errors import AppError, ErrorCode
from kokogram_shared.logging import get_request_id

from gateway.app.ports.users_client import UsersClient


class HttpUsersClient(UsersClient):
    def __init__(
        self,
        base_url: str,
        client: httpx.AsyncClient | None = None,
        timeout: float = 5.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client
        self._timeout = timeout

    async def verify_session(self, token: str) -> str | None:
        url = f"{self._base_url}/internal/sessions/verify"
        client = self._client or httpx.AsyncClient()
        should_close = self._client is None

        headers = {}
        request_id = get_request_id()
        if request_id:
            headers["X-Request-ID"] = request_id

        try:
            response = await client.post(
                url,
                json={"token": token},
                headers=headers,
                timeout=self._timeout,
            )
            if response.status_code == 200:
                data = response.json()
                user_id = data.get("user_id")
                return str(user_id) if user_id is not None else None
            if response.status_code == 401:
                return None
            if response.status_code == 503:
                raise AppError(ErrorCode.SERVICE_UNAVAILABLE)
            raise AppError(ErrorCode.SERVICE_UNAVAILABLE)
        except httpx.RequestError as exc:
            raise AppError(ErrorCode.SERVICE_UNAVAILABLE) from exc
        finally:
            if should_close:
                await client.aclose()
