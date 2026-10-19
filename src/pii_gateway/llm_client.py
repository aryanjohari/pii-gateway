"""Shared HTTP client for the upstream LLM."""

from http.cookiejar import CookieJar, DefaultCookiePolicy

import httpx


def create_llm_client(
    base_url: str,
    timeout_seconds: float,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> httpx.AsyncClient:
    """Build the one client every caller shares.

    Cookies are blocked: a shared client would otherwise store a cookie the upstream set for
    one caller and send it with other callers' requests. ``transport`` is httpx's own seam,
    used to swap in a fake upstream.
    """
    block_all_cookies = CookieJar(policy=DefaultCookiePolicy(allowed_domains=[]))
    return httpx.AsyncClient(
        base_url=base_url, timeout=timeout_seconds, cookies=block_all_cookies, transport=transport
    )
