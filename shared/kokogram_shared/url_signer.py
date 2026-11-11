import hashlib
import hmac
from datetime import timedelta
from urllib.parse import urlencode

from kokogram_shared.clock import Clock
from kokogram_shared.errors import AppError, ErrorCode


class UrlSigner:
    def __init__(
        self,
        secret: str | bytes,
        clock: Clock,
        ttl: timedelta | int = timedelta(minutes=15),
    ) -> None:
        if isinstance(secret, str):
            secret = secret.encode("utf-8")
        if not secret:
            raise ValueError("secret не может быть пустым")
        self._secret = secret
        self._clock = clock
        self._ttl_seconds = int(ttl.total_seconds()) if isinstance(ttl, timedelta) else int(ttl)
        if self._ttl_seconds <= 0:
            raise ValueError("ttl должен быть положительным")

    def sign(self, path: str, extra: dict[str, str] | None = None) -> str:
        clean_path = _normalize_path(path)
        expires = int(self._clock.now().timestamp()) + self._ttl_seconds
        sig = self._compute_sig(clean_path, expires, extra)

        params: dict[str, str | int] = {}
        if extra:
            for key in sorted(extra):
                params[key] = extra[key]
        params["expires"] = expires
        params["sig"] = sig
        return f"{clean_path}?{urlencode(params)}"

    def verify(
        self,
        path: str,
        expires: int | str,
        sig: str,
        extra: dict[str, str] | None = None,
    ) -> None:
        clean_path = _normalize_path(path)
        try:
            expires_ts = int(expires)
        except (TypeError, ValueError) as exc:
            raise AppError(ErrorCode.UNAUTHORIZED) from exc

        if not sig:
            raise AppError(ErrorCode.UNAUTHORIZED)

        now_ts = int(self._clock.now().timestamp())
        if now_ts >= expires_ts:
            raise AppError(ErrorCode.UNAUTHORIZED)

        expected = self._compute_sig(clean_path, expires_ts, extra)
        if not hmac.compare_digest(sig.lower(), expected):
            raise AppError(ErrorCode.UNAUTHORIZED)

    def _compute_sig(
        self,
        clean_path: str,
        expires: int,
        extra: dict[str, str] | None = None,
    ) -> str:
        lines = [clean_path, str(expires)]
        if extra:
            for key in sorted(extra):
                lines.append(f"{key}={extra[key]}")
        payload = "\n".join(lines).encode("utf-8")
        return hmac.new(self._secret, payload, hashlib.sha256).hexdigest()


def _normalize_path(path: str) -> str:
    if path.startswith("/api/v1/"):
        path = path[len("/api/v1") :]
    elif path == "/api/v1":
        path = "/"
    if not path.startswith("/"):
        path = "/" + path
    return path
