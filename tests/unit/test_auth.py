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


def test_sanitize_unavailable_when_api_key_unset() -> None:
    req = MagicMock()
    req.headers = {}
    s = Settings.model_construct(sanitize_http_api_key=None)
    with pytest.raises(HTTPException) as ei:
        verify_http_auth(req, s)
    assert ei.value.status_code == 503
    assert isinstance(ei.value.detail, dict)
    assert ei.value.detail["code"] == "misconfigured"


def test_sanitize_unavailable_when_api_key_empty() -> None:
    req = MagicMock()
    req.headers = {}
    s = Settings.model_construct(sanitize_http_api_key="")
    with pytest.raises(HTTPException) as ei:
        verify_http_auth(req, s)
    assert ei.value.status_code == 503


def test_sanitize_unavailable_when_api_key_whitespace_only() -> None:
    req = MagicMock()
    req.headers = {}
    s = Settings.model_construct(sanitize_http_api_key="   ")
    with pytest.raises(HTTPException) as ei:
        verify_http_auth(req, s)
    assert ei.value.status_code == 503
