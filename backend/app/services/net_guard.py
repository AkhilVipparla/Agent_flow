"""SSRF guard for visitor-supplied hosts (LLM base URL, database host)."""
from __future__ import annotations

import ipaddress
import socket


class HostNotAllowedError(ValueError):
    pass


def assert_public_host(host: str | None, port: int) -> None:
    from app.config import settings

    if not host:
        raise HostNotAllowedError("Host is missing.")
    if settings.allow_private_hosts:
        return
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise HostNotAllowedError("Could not resolve the host.") from None
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_unspecified:
            raise HostNotAllowedError("Host must be a public address.")
