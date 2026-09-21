"""In-process sliding-window rate limiter (no external store)."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable


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
