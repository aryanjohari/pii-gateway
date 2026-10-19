"""Unit tests for in-process rate limiter."""

from pii_gateway.api.rate_limit import (
    client_rate_limit_key,
    create_sliding_window_limiter,
    resolve_client_host,
)


def test_limiter_allows_under_cap() -> None:
    allow = create_sliding_window_limiter(3, 60.0)
    assert allow("a") is True
    assert allow("a") is True
    assert allow("a") is True


def test_limiter_blocks_over_cap() -> None:
    allow = create_sliding_window_limiter(2, 60.0)
    assert allow("b") is True
    assert allow("b") is True
    assert allow("b") is False


def test_limiter_disabled_when_zero() -> None:
    allow = create_sliding_window_limiter(0, 60.0)
    for _ in range(20):
        assert allow("c") is True


def test_limiter_isolates_keys() -> None:
    allow = create_sliding_window_limiter(1, 60.0)
    assert allow("x") is True
    assert allow("x") is False
    assert allow("y") is True


def test_client_rate_limit_key() -> None:
    assert client_rate_limit_key("1.2.3.4", True) == "1.2.3.4:authed"
    assert client_rate_limit_key(None, False) == "unknown:anon"


def test_resolve_client_host_ignores_header_when_setting_empty() -> None:
    headers = {"CF-Connecting-IP": "9.9.9.9"}
    assert resolve_client_host("1.2.3.4", headers, "") == "1.2.3.4"


def test_resolve_client_host_uses_trusted_header() -> None:
    headers = {"CF-Connecting-IP": " 9.9.9.9 "}
    assert resolve_client_host("1.2.3.4", headers, "CF-Connecting-IP") == "9.9.9.9"


def test_resolve_client_host_takes_first_entry_of_forwarded_list() -> None:
    headers = {"X-Forwarded-For": "9.9.9.9, 10.0.0.1"}
    assert resolve_client_host("1.2.3.4", headers, "X-Forwarded-For") == "9.9.9.9"


def test_resolve_client_host_falls_back_when_header_missing_or_blank() -> None:
    blank = {"CF-Connecting-IP": " "}
    assert resolve_client_host("1.2.3.4", {}, "CF-Connecting-IP") == "1.2.3.4"
    assert resolve_client_host("1.2.3.4", blank, "CF-Connecting-IP") == "1.2.3.4"
    assert resolve_client_host(None, {}, "CF-Connecting-IP") is None
