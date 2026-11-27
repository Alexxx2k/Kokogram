from collections.abc import Mapping
from enum import StrEnum


class ServiceTarget(StrEnum):
    USERS = "users"
    CHATS = "chats"
    MESSAGES = "messages"
    GIF = "gif"


class RouteTable:
    API_PREFIX = "/api/v1"

    @staticmethod
    def strip_api_prefix(path: str) -> str:
        raw_path = path.split("?")[0].strip()
        if raw_path.startswith("/api/v1/"):
            raw_path = raw_path[len("/api/v1") :]
        elif raw_path == "/api/v1":
            raw_path = "/"
        if not raw_path.startswith("/") and raw_path:
            raw_path = "/" + raw_path
        return raw_path or "/"

    @staticmethod
    def is_internal(path: str) -> bool:
        clean = RouteTable.strip_api_prefix(path)
        segments = [s for s in clean.strip("/").split("/") if s]
        return bool(segments and segments[0] == "internal")

    def match_service(self, path: str) -> ServiceTarget | None:
        clean = self.strip_api_prefix(path)
        segments = [s for s in clean.strip("/").split("/") if s]
        if not segments:
            return None

        first = segments[0]

        if first in ("auth", "users", "contacts", "blocks"):
            return ServiceTarget.USERS

        if first == "messages":
            return ServiceTarget.MESSAGES

        if first == "gifs":
            return ServiceTarget.GIF

        if first == "chats":
            if len(segments) >= 3 and segments[2] in ("messages", "read"):
                return ServiceTarget.MESSAGES
            return ServiceTarget.CHATS

        return None

    @staticmethod
    def is_public_endpoint(method: str, path: str) -> bool:
        if method.upper() != "POST":
            return False

        clean = RouteTable.strip_api_prefix(path).rstrip("/")
        return clean in ("/auth/register", "/auth/login")

    @staticmethod
    def is_signed_url(method: str, path: str, query_params: Mapping[str, str]) -> bool:
        if method.upper() != "GET":
            return False

        sig = query_params.get("sig")
        expires = query_params.get("expires")
        if not sig or not expires:
            return False

        clean = RouteTable.strip_api_prefix(path)
        segments = [s for s in clean.strip("/").split("/") if s]
        if len(segments) == 3:
            if segments[0] in ("users", "chats") and segments[2] == "avatar":
                return True
            if segments[0] == "messages" and segments[2] in ("attachment", "preview"):
                return True

        return False
