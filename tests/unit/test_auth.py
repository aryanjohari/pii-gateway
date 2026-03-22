"""HTTP auth unit tests."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from pii_gateway.api.auth import verify_http_auth
from pii_gateway.settings import Settings


def test_api_key_success() -> None:
    req = MagicMock()
    req.headers = {"X-API-Key": "secret"}
    s = Settings.model_construct(sanitize_http_api_key="secret")
    verify_http_auth(req, s)


def test_api_key_failure() -> None:
    req = MagicMock()
    req.headers = {"X-API-Key": "wrong"}
    s = Settings.model_construct(sanitize_http_api_key="secret")
    with pytest.raises(HTTPException) as ei:
        verify_http_auth(req, s)
    assert ei.value.status_code == 401


def test_basic_success() -> None:
    import base64

    token = base64.b64encode(b"user:pass").decode("ascii")
    req = MagicMock()
    req.headers = {"Authorization": f"Basic {token}"}
    s = Settings.model_construct(
        sanitize_http_api_key=None,
        basic_auth_user="user",
        basic_auth_password="pass",
    )
    verify_http_auth(req, s)


def test_open_when_unconfigured() -> None:
    req = MagicMock()
    req.headers = {}
    s = Settings.model_construct(
        sanitize_http_api_key=None,
        basic_auth_user=None,
        basic_auth_password=None,
    )
    verify_http_auth(req, s)
