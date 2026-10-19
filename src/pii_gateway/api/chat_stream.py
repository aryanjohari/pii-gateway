"""Relay an upstream server-sent-event stream to the caller.

The request was redacted before it was sent, so this only moves bytes. It never logs them.
"""

import json
import logging
from collections.abc import AsyncIterator

import httpx

from pii_gateway.logging_config import get_logger, log_event

logger = get_logger(__name__)


async def relay_stream(upstream: httpx.Response, host: str, cid: str) -> AsyncIterator[bytes]:
    """Yield the upstream's chunks unchanged and always close the upstream request.

    The generator is closed when the caller disconnects, which releases the upstream
    connection. If the upstream breaks mid-stream the status line is already sent, so the
    failure is reported as a final error event, the way OpenAI reports mid-stream errors.
    """
    try:
        async for chunk in upstream.aiter_bytes():
            yield chunk
    except httpx.RequestError:
        log_event(
            logger,
            logging.WARNING,
            "chat_stream_interrupted",
            correlation_id=cid,
            adapter="openai_chat",
            error_code="upstream_stream_interrupted",
        )
        yield _error_event(host)
    finally:
        await upstream.aclose()


def _error_event(host: str) -> bytes:
    error = {
        "message": f"Stream from upstream {host} was interrupted",
        "type": "server_error",
        "param": None,
        "code": "upstream_stream_interrupted",
    }
    return f"data: {json.dumps({'error': error})}\n\n".encode()
