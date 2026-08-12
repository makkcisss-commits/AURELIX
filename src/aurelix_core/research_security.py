from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
from urllib.parse import urlparse


@dataclass(frozen=True)
class FetchPolicy:
    allowed_schemes: frozenset[str] = frozenset({"https"})
    max_bytes: int = 5_000_000
    max_redirects: int = 3
    timeout_seconds: float = 15.0


def validate_research_url(url: str, policy: FetchPolicy = FetchPolicy()) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in policy.allowed_schemes:
        raise ValueError("research fetch requires an allowed URL scheme")
    if not parsed.hostname:
        raise ValueError("research URL must contain a hostname")
    if parsed.username or parsed.password:
        raise ValueError("embedded URL credentials are not allowed")
    try:
        address = ip_address(parsed.hostname)
    except ValueError:
        address = None
    if address and (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved):
        raise ValueError("private or reserved IP targets are not allowed")
    return parsed.geturl()


def validate_content_size(content_length: int | None, policy: FetchPolicy = FetchPolicy()) -> None:
    if content_length is not None and content_length > policy.max_bytes:
        raise ValueError("research response exceeds configured size limit")
