import ipaddress
import socket

import pytest


@pytest.fixture(autouse=True)
def no_external_network(monkeypatch):
    """Tests may use local ASGI plumbing; archive calls must be mocked."""
    original = socket.getaddrinfo

    def local_only(host, *args, **kwargs):
        if host not in (None, "localhost", b"localhost"):
            value = host.decode() if isinstance(host, bytes) else host
            try:
                allowed = ipaddress.ip_address(value).is_loopback
            except ValueError:
                allowed = False
            if not allowed:
                raise AssertionError(f"External network is disabled in tests: {host}")
        return original(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", local_only)
