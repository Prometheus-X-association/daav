"""Protection against Server-Side Request Forgery for user-supplied URLs.

Two levels of checks:
- check_url_static: syntax-only check run by the Pydantic validators (scheme, localhost,
  literal private IPs). It never touches the network, so stored datasets always load.
- ensure_public_url: run right before connecting; resolves the hostname and refuses any
  address that is private, loopback, link-local or reserved.

Hosts listed in the ALLOWED_PRIVATE_HOSTS setting bypass both checks (e.g. a docker-compose
service such as "elasticsearch", or a local test node).
"""
import ipaddress
import socket
from typing import Optional
from urllib.parse import urlparse


class SsrfError(ValueError):
    """Raised when a URL points to a forbidden destination."""


def _allowed_private_hosts() -> set:
    from app.config.settings import settings
    return {h.strip().lower() for h in (settings.allowed_private_hosts or []) if h and h.strip()}


def _is_internal_ip(ip: ipaddress._BaseAddress) -> bool:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_unspecified
        or ip.is_reserved
        or ip.is_multicast
    )


def _parse(value: str, field_name: str):
    try:
        parsed = urlparse(value)
    except Exception:
        raise SsrfError(f"'{field_name}' is not a valid URL.")
    if parsed.scheme not in ('http', 'https'):
        raise SsrfError(f"'{field_name}' must use http or https scheme.")
    return parsed


def check_url_static(value: Optional[str], field_name: str) -> Optional[str]:
    """Validate a URL without network access. Returns the value unchanged."""
    if not value:
        return value
    parsed = _parse(value, field_name)
    hostname = (parsed.hostname or '').lower()
    if hostname and hostname in _allowed_private_hosts():
        return value
    if hostname in ('localhost', '0.0.0.0', ''):
        raise SsrfError(f"'{field_name}' must not point to localhost.")
    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        return value  # hostname, resolved later by ensure_public_url
    if _is_internal_ip(ip):
        raise SsrfError(f"'{field_name}' must not point to a private or internal address.")
    return value


def ensure_public_url(value: str, field_name: str = 'url') -> None:
    """Resolve the URL hostname and refuse internal destinations.

    Raises:
        SsrfError: if the URL is invalid, unresolvable or resolves to an internal address.
    """
    check_url_static(value, field_name)
    parsed = _parse(value, field_name)
    hostname = (parsed.hostname or '').lower()
    if hostname in _allowed_private_hosts():
        return
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    try:
        infos = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise SsrfError(f"Cannot resolve host '{hostname}': {e}")
    for info in infos:
        if _is_internal_ip(ipaddress.ip_address(info[4][0])):
            raise SsrfError(
                f"'{field_name}' resolves to a private or internal address. "
                f"Add '{hostname}' to ALLOWED_PRIVATE_HOSTS if this is intended."
            )
