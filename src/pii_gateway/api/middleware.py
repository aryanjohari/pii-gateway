"""Request middleware: correlation ID propagation."""

import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

CORRELATION_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        cid = request.headers.get(CORRELATION_HEADER)
        if not cid:
            cid = str(uuid.uuid4())
        request.state.correlation_id = cid
        response = await call_next(request)
        response.headers[CORRELATION_HEADER] = cid
        return response


def get_correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", str(uuid.uuid4()))
