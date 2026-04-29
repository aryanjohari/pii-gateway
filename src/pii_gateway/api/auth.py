"""HTTP API authentication for the sanitize route (API key)."""

import secrets

from fastapi import HTTPException, Request, status

from pii_gateway.settings import Settings


def verify_http_auth(request: Request, settings: Settings) -> None:
    """Require ``X-API-Key`` matching ``SANITIZE_HTTP_API_KEY`` (constant-time)."""
    raw = settings.sanitize_http_api_key
    if raw is None or not raw.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "misconfigured",
                "message": "SANITIZE_HTTP_API_KEY is not set",
            },
        )
    expected = raw.strip()
    provided = request.headers.get("X-API-Key")
    if not _const_eq(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "Invalid or missing API key"},
        )


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
