"""HTTP API authentication (API key or Basic)."""

import base64
import binascii
import secrets

from fastapi import HTTPException, Request, status

from pii_gateway.settings import Settings


def verify_http_auth(request: Request, settings: Settings) -> None:
    """Require API key or Basic when configured; allow open access if neither is set (dev only)."""
    if settings.sanitize_http_api_key:
        provided = request.headers.get("X-API-Key")
        if not _const_eq(provided, settings.sanitize_http_api_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "unauthorized", "message": "Invalid or missing API key"},
            )
        return

    if settings.basic_auth_user and settings.basic_auth_password:
        user, pw = _parse_basic(request.headers.get("Authorization"))
        if user is None or pw is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "unauthorized", "message": "Missing Basic credentials"},
            )
        if not _const_eq(user, settings.basic_auth_user) or not _const_eq(
            pw, settings.basic_auth_password
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "forbidden", "message": "Invalid credentials"},
            )
        return


def verify_internal_job(request: Request, settings: Settings) -> None:
    if not settings.internal_job_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "disabled", "message": "Internal jobs are not enabled"},
        )
    provided = request.headers.get("X-Internal-Job-Key")
    if not _const_eq(provided, settings.internal_job_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "Invalid internal job key"},
        )


def _const_eq(a: str | None, b: str) -> bool:
    if a is None:
        return False
    return secrets.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def _parse_basic(header: str | None) -> tuple[str | None, str | None]:
    if not header or not header.startswith("Basic "):
        return None, None
    try:
        raw = base64.b64decode(header[6:].strip(), validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return None, None
    if ":" not in raw:
        return None, None
    user, _, password = raw.partition(":")
    return user, password
