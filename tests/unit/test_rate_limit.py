"""Unit tests for in-process rate limiter."""

from pii_gateway.api.rate_limit import client_rate_limit_key, create_sliding_window_limiter


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
