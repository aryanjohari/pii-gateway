"""OpenAI-compatible chat-completions proxy: redact message text, then forward upstream."""

import logging
import time
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from pii_gateway.api.auth import verify_http_auth
from pii_gateway.api.chat_redaction import message_texts, redact_chat_messages
from pii_gateway.api.chat_schemas import ChatCompletionRequest
from pii_gateway.api.middleware import get_correlation_id
from pii_gateway.api.rate_limit import client_rate_limit_key
from pii_gateway.api.request_limits import enforce_content_length
from pii_gateway.logging_config import get_logger, log_event
from pii_gateway.settings import Settings

logger = get_logger(__name__)
router = APIRouter(tags=["chat"])

_REJECTION_CODES = {"unsupported_content_type", "unsupported_field", "streaming_not_supported"}


@router.post("/v1/chat/completions")
async def chat_completions(request: Request) -> JSONResponse:
    try:
        return await _proxy(request)
    except HTTPException as exc:
        return _openai_error(exc)


async def _proxy(request: Request) -> JSONResponse:
    settings: Settings = request.app.state.settings
    enforce_content_length(request, settings)
    _enforce_rate_limit(request)
    verify_http_auth(request, settings)

    upstream_authorization = request.headers.get("Authorization")
    if not upstream_authorization:
        raise _error(
            status.HTTP_401_UNAUTHORIZED,
            "missing_upstream_key",
            "Send the upstream API key in the Authorization header",
        )
    llm_client: httpx.AsyncClient | None = request.app.state.llm_client
    if llm_client is None:
        raise _error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "misconfigured",
            "LLM_UPSTREAM_BASE_URL is not set",
        )

    raw_body = await request.body()
    chat_request = _parse_request(raw_body, settings)

    policy = request.app.state.policy
    cid = get_correlation_id(request)
    t0 = time.monotonic()
    try:
        cleaned, summary = redact_chat_messages(
            chat_request.messages,
            analyzer=request.app.state.analyzer,
            anonymizer=request.app.state.anonymizer,
            entity_types=policy.redaction_entities,
        )
    except Exception:
        log_event(
            logger,
            logging.ERROR,
            "chat_redaction_failed",
            correlation_id=cid,
            adapter="openai_chat",
            error_code="redaction_error",
        )
        raise _error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal_error",
            "Redaction failed; nothing was forwarded",
        ) from None

    payload = chat_request.model_copy(update={"messages": cleaned}).model_dump(exclude_unset=True)
    upstream = await llm_client.post(
        "chat/completions", json=payload, headers={"Authorization": upstream_authorization}
    )

    log_event(
        logger,
        logging.INFO,
        "chat_complete",
        correlation_id=cid,
        adapter="openai_chat",
        config_version=policy.config_version,
        duration_ms=int((time.monotonic() - t0) * 1000),
        message_count=len(cleaned),
        entity_summary=summary,
        http_status=upstream.status_code,
    )
    return JSONResponse(status_code=upstream.status_code, content=upstream.json())


def _parse_request(raw_body: bytes, settings: Settings) -> ChatCompletionRequest:
    if 0 < settings.sanitize_max_body_bytes < len(raw_body):
        raise _error(
            status.HTTP_413_CONTENT_TOO_LARGE,
            "payload_too_large",
            "Request body exceeds size limit",
        )
    try:
        chat_request = ChatCompletionRequest.model_validate_json(raw_body)
    except ValidationError as exc:
        # include_input=False: error entries must never carry message text.
        first = exc.errors(include_input=False)[0]
        if first["type"] == "json_invalid":
            raise _error(422, "invalid_json", "Request body is not valid JSON") from None
        if first["type"] in _REJECTION_CODES:
            raise _error(422, first["type"], first["msg"]) from None
        raise _error(422, "invalid_request", "Invalid request body") from None

    max_chars = settings.sanitize_max_chars
    total = sum(len(text) for message in chat_request.messages for text in message_texts(message))
    if 0 < max_chars < total:
        raise _error(
            status.HTTP_413_CONTENT_TOO_LARGE,
            "payload_too_large",
            "Payload exceeds character limit",
        )
    return chat_request


def _enforce_rate_limit(request: Request) -> None:
    rate_allow = getattr(request.app.state, "sanitize_rate_allow", None)
    if not callable(rate_allow):
        return
    client = request.client.host if request.client else None
    key = client_rate_limit_key(client, bool(request.headers.get("X-API-Key")))
    if not rate_allow(key):
        raise _error(
            status.HTTP_429_TOO_MANY_REQUESTS, "rate_limited", "Too many requests; try again later"
        )


def _error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _openai_error(exc: HTTPException) -> JSONResponse:
    """Re-shape a gateway error as ``{"error": {message, type, param, code}}`` for OpenAI SDKs."""
    detail: Any = exc.detail
    if not (isinstance(detail, dict) and "code" in detail and "message" in detail):
        detail = {"code": "http_error", "message": "Request failed"}
    error_type = "invalid_request_error" if exc.status_code < 500 else "server_error"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": str(detail["message"]),
                "type": error_type,
                "param": None,
                "code": str(detail["code"]),
            }
        },
    )
