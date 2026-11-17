from urllib.parse import urlparse
import ipaddress
from typing import Tuple


def validate_url(url: str, allowed_hosts: list[str]) -> Tuple[bool, str | None]:
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "invalid_url"

    if parsed.scheme != "https":
        return False, "invalid_url"

    if parsed.port is not None and parsed.port != 443:
        return False, "invalid_url"

    if parsed.username or parsed.password:
        return False, "invalid_url"

    if not parsed.hostname:
        return False, "invalid_url"

    try:
        ipaddress.ip_address(parsed.hostname)
        return False, "invalid_url"
    except ValueError:
        pass

    hostname = parsed.hostname.lower()
    is_allowed = False
    for allowed in allowed_hosts:
        allowed = allowed.lower()
        if hostname == allowed or hostname.endswith("." + allowed):
            is_allowed = True
            break

    if not is_allowed:
        return False, "host_not_allowed"

    return True, None
