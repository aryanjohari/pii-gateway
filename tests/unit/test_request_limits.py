"""Unit tests for sanitize payload size / char budget."""

import pytest
from fastapi import HTTPException

from pii_gateway.api.request_limits import enforce_char_budget
from pii_gateway.api.schemas import SanitizeRequest
from pii_gateway.settings import Settings


def test_char_budget_allows_small_payload() -> None:
    settings = Settings(sanitize_max_chars=100)
    body = SanitizeRequest(text="hello")
    enforce_char_budget(body, settings)


def test_char_budget_rejects_large_text() -> None:
    settings = Settings(sanitize_max_chars=10)
    body = SanitizeRequest(text="x" * 20)
    with pytest.raises(HTTPException) as exc:
        enforce_char_budget(body, settings)
    assert exc.value.status_code == 413
    detail = exc.value.detail
    assert isinstance(detail, dict)
    assert detail["code"] == "payload_too_large"


def test_char_budget_counts_structured_strings() -> None:
    settings = Settings(sanitize_max_chars=15)
    body = SanitizeRequest(structured={"note": "a" * 20})
    with pytest.raises(HTTPException) as exc:
        enforce_char_budget(body, settings)
    assert exc.value.status_code == 413


def test_char_budget_disabled_when_zero() -> None:
    settings = Settings(sanitize_max_chars=0)
    body = SanitizeRequest(text="z" * 50_000)
    enforce_char_budget(body, settings)
