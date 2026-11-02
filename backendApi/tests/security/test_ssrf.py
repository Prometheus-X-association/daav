"""
Security tests for SSRF protection (static URL checks, DNS resolution, allowlist).
"""
import socket

import pytest

from app.config.settings import settings
from app.utils import ssrf
from app.utils.ssrf import SsrfError, check_url_static, ensure_public_url


def _addrinfo(*ips):
    return [(socket.AF_INET6 if ':' in ip else socket.AF_INET, socket.SOCK_STREAM, 6, '', (ip, 9200)) for ip in ips]


@pytest.fixture
def allowlist(monkeypatch):
    def set_hosts(*hosts):
        monkeypatch.setattr(settings, 'allowed_private_hosts', list(hosts))
    set_hosts()
    return set_hosts


class TestCheckUrlStatic:

    @pytest.mark.parametrize("url", [
        "http://[::ffff:127.0.0.1]:9200",
        "http://[::1]:9200",
    ])
    def test_ipv6_loopback_forms_rejected(self, url, allowlist):
        with pytest.raises(SsrfError):
            check_url_static(url, 'url')

    def test_hostname_is_not_resolved(self, allowlist, monkeypatch):
        monkeypatch.setattr(socket, 'getaddrinfo', lambda *a, **k: pytest.fail("must not resolve"))
        assert check_url_static("http://es.example.com:9200", 'url') == "http://es.example.com:9200"

    def test_allowlisted_localhost_accepted(self, allowlist):
        allowlist('localhost')
        assert check_url_static("http://localhost:9200", 'url') == "http://localhost:9200"

    def test_allowlisted_private_ip_accepted(self, allowlist):
        allowlist('10.0.0.5')
        assert check_url_static("http://10.0.0.5:9200", 'url') == "http://10.0.0.5:9200"

    def test_allowlist_is_case_insensitive(self, allowlist):
        allowlist('MyHost')
        assert check_url_static("http://myhost:9200", 'url')

    def test_other_private_ip_still_rejected_with_allowlist(self, allowlist):
        allowlist('10.0.0.5')
        with pytest.raises(SsrfError):
            check_url_static("http://10.0.0.6:9200", 'url')


class TestEnsurePublicUrl:

    def test_public_resolution_accepted(self, allowlist, monkeypatch):
        monkeypatch.setattr(socket, 'getaddrinfo', lambda *a, **k: _addrinfo('93.184.216.34'))
        ensure_public_url("https://es.example.com")

    @pytest.mark.parametrize("ip", ['127.0.1.1', '10.1.2.3', '192.168.1.10', '169.254.169.254', '::1', 'fd00::1'])
    def test_hostname_resolving_to_internal_ip_rejected(self, ip, allowlist, monkeypatch):
        monkeypatch.setattr(socket, 'getaddrinfo', lambda *a, **k: _addrinfo(ip))
        with pytest.raises(SsrfError, match="ALLOWED_PRIVATE_HOSTS"):
            ensure_public_url("http://innocent.example.com:9200")

    def test_any_internal_address_among_several_rejected(self, allowlist, monkeypatch):
        monkeypatch.setattr(socket, 'getaddrinfo', lambda *a, **k: _addrinfo('93.184.216.34', '10.0.0.1'))
        with pytest.raises(SsrfError):
            ensure_public_url("http://mixed.example.com")

    def test_allowlisted_host_not_resolved(self, allowlist, monkeypatch):
        allowlist('elasticsearch')
        monkeypatch.setattr(socket, 'getaddrinfo', lambda *a, **k: pytest.fail("must not resolve"))
        ensure_public_url("http://elasticsearch:9200")

    def test_unresolvable_host_rejected(self, allowlist, monkeypatch):
        def fail(*a, **k):
            raise socket.gaierror("Name or service not known")
        monkeypatch.setattr(socket, 'getaddrinfo', fail)
        with pytest.raises(SsrfError, match="Cannot resolve"):
            ensure_public_url("http://does-not-exist.example")

    def test_static_checks_still_apply(self, allowlist):
        with pytest.raises(SsrfError):
            ensure_public_url("ftp://example.com")

    def test_default_port_used_for_resolution(self, allowlist, monkeypatch):
        calls = []
        def record(host, port, **k):
            calls.append((host, port))
            return _addrinfo('93.184.216.34')
        monkeypatch.setattr(socket, 'getaddrinfo', record)
        ensure_public_url("https://es.example.com")
        assert calls == [('es.example.com', 443)]
