"""In-process sliding-window rate limiter (no external store)."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Mapping


def create_sliding_window_limiter(
    max_requests: int,
    window_seconds: float,
) -> Callable[[str], bool]:
    """Return ``allow(key)`` — True if the request is within the limit.

    ``max_requests <= 0`` disables limiting (always allows).
    """
    lock = threading.Lock()
    hits: dict[str, list[float]] = {}

    def allow(key: str) -> bool:
        if max_requests <= 0:
            return True
        now = time.monotonic()
        cutoff = now - window_seconds
        with lock:
            times = [t for t in hits.get(key, []) if t > cutoff]
            if len(times) >= max_requests:
                hits[key] = times
                return False
            times.append(now)
            hits[key] = times
            return True

    return allow


def client_rate_limit_key(client_host: str | None, api_key_present: bool) -> str:
    """Bucket by client IP; fall back to a shared anonymous bucket."""
    host = (client_host or "").strip() or "unknown"
    suffix = "authed" if api_key_present else "anon"
    return f"{host}:{suffix}"


def resolve_client_host(
    direct_host: str | None,
    headers: Mapping[str, str],
    trusted_header: str,
) -> str | None:
    """Return the client host to rate-limit on.

    The header is read only when ``trusted_header`` names one: any client can send any header,
    so trusting one by default would let callers dodge limits by rotating its value. Only set
    it when a proxy you control overwrites the header and the app is not reachable around it.
    """
    if not trusted_header:
        return direct_host
    forwarded = headers.get(trusted_header, "").split(",")[0].strip()
    return forwarded or direct_host
