"""Realtime JSON sanitize endpoint."""

import json
import logging
import time

from fastapi import APIRouter, HTTPException, Request, status

from pii_gateway.api.auth import verify_http_auth
from pii_gateway.api.middleware import get_correlation_id
from pii_gateway.api.schemas import SanitizeRequest, SanitizeSuccessResponse
from pii_gateway.core.sanitize_pipeline import sanitize_payload
from pii_gateway.logging_config import get_logger, log_event
from pii_gateway.storage.paths import artifact_relative_key

logger = get_logger(__name__)
router = APIRouter(tags=["sanitize"])


@router.post("/v1/sanitize", response_model=SanitizeSuccessResponse)
async def sanitize(request: Request, body: SanitizeRequest) -> SanitizeSuccessResponse:
    settings = request.app.state.settings
    verify_http_auth(request, settings)
    policy = request.app.state.policy
    analyzer = request.app.state.analyzer
    anonymizer = request.app.state.anonymizer
    storage = request.app.state.storage

    t0 = time.monotonic()
    cid = get_correlation_id(request)

    try:
        result, summary = sanitize_payload(
            text=body.text,
            structured=body.structured,
            policy=policy,
            analyzer=analyzer,
            anonymizer=anonymizer,
        )
    except Exception:
        log_event(
            logger,
            logging.ERROR,
            "sanitize_failed",
            correlation_id=cid,
            adapter="http_json",
            config_version=policy.config_version,
            error_code="sanitize_error",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "internal_error", "message": "Sanitization failed"},
        ) from None

    duration_ms = int((time.monotonic() - t0) * 1000)
    rel = artifact_relative_key("http", cid, "json")

    if policy.persistence.write_raw:
        raw_blob = json.dumps(
            {"text": body.text, "structured": body.structured},
            default=str,
        ).encode("utf-8")
        await storage.write_artifact("raw", rel, raw_blob, "application/json")

    if policy.persistence.write_cleaned:
        cleaned_blob = json.dumps(
            {"result": result, "entity_summary": summary},
            default=str,
        ).encode("utf-8")
        await storage.write_artifact("cleaned", rel, cleaned_blob, "application/json")

    detections = int(sum(summary.values())) if summary else 0
    log_event(
        logger,
        logging.INFO,
        "sanitize_complete",
        correlation_id=cid,
        adapter="http_json",
        config_version=policy.config_version,
        duration_ms=duration_ms,
        row_count=detections,
    )

    return SanitizeSuccessResponse(
        correlation_id=cid,
        adapter="http_json",
        config_version=policy.config_version,
        result=result,
        meta={"entity_summary": summary, "duration_ms": duration_ms},
    )
