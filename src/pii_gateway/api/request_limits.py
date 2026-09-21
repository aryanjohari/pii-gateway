"""Sanitize request size / character budget checks (no raw body logging)."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request, status

from pii_gateway.api.schemas import SanitizeRequest
from pii_gateway.settings import Settings


def enforce_content_length(request: Request, settings: Settings) -> None:
    """Reject when ``Content-Length`` exceeds ``sanitize_max_body_bytes``."""
    max_bytes = settings.sanitize_max_body_bytes
    if max_bytes <= 0:
        return
    raw = request.headers.get("content-length")
    if raw is None:
        return
    try:
        length = int(raw)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_content_length", "message": "Invalid Content-Length"},
        ) from None
    if length > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail={
                "code": "payload_too_large",
                "message": "Request body exceeds size limit",
            },
        )


def _count_chars(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, str):
        return len(value)
    if isinstance(value, dict):
        return sum(_count_chars(k) + _count_chars(v) for k, v in value.items())
    if isinstance(value, list):
        return sum(_count_chars(item) for item in value)
    return 0


def enforce_char_budget(body: SanitizeRequest, settings: Settings) -> None:
    """Reject when total string characters exceed ``sanitize_max_chars``."""
    max_chars = settings.sanitize_max_chars
    if max_chars <= 0:
        return
    total = _count_chars(body.text) + _count_chars(body.structured)
    if total > max_chars:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail={
                "code": "payload_too_large",
                "message": "Payload exceeds character limit",
            },
        )
