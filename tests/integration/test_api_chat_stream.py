"""POST /v1/chat/completions with stream=true against a fake streaming upstream."""

import json
from collections.abc import Callable

import httpx
from starlette.testclient import TestClient

HEADERS = {"X-API-Key": "test-key", "Authorization": "Bearer sk-caller-secret"}
EMAIL = "alice@example.com"
EVENTS = b'data: {"choices":[{"delta":{"content":"Hello <EMAIL_ADDRESS>"}}]}\n\ndata: [DONE]\n\n'
InstallUpstream = Callable[[Callable[[httpx.Request], httpx.Response]], list[httpx.Request]]


def _body(**extra: object) -> dict[str, object]:
    return {
        "model": "m",
        "messages": [{"role": "user", "content": f"Please email {EMAIL}"}],
        "stream": True,
        **extra,
    }


def _event_stream_response(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200, headers={"content-type": "text/event-stream"}, stream=httpx.ByteStream(EVENTS)
    )


def test_stream_is_redacted_going_out_and_relayed_coming_back(
    chat_client: TestClient, install_upstream: InstallUpstream
) -> None:
    calls = install_upstream(_event_stream_response)
    r = chat_client.post(
        "/v1/chat/completions",
        headers=HEADERS,
        json=_body(stream_options={"include_usage": True}),
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    assert r.content == EVENTS
    sent = json.loads(calls[0].content)
    assert sent["stream"] is True
    assert sent["stream_options"] == {"include_usage": True}
    assert EMAIL not in calls[0].content.decode()
    assert "<EMAIL_ADDRESS>" in sent["messages"][0]["content"]
    assert calls[0].headers["Authorization"] == "Bearer sk-caller-secret"


def test_upstream_error_before_the_stream_starts_is_replaced(
    chat_client: TestClient, install_upstream: InstallUpstream
) -> None:
    echoed = {"error": {"message": f"bad prompt from {EMAIL}"}}
    install_upstream(lambda request: httpx.Response(429, json=echoed))
    r = chat_client.post("/v1/chat/completions", headers=HEADERS, json=_body())
    assert r.status_code == 429
    assert r.json()["error"]["code"] == "upstream_error"
    assert "alice" not in r.text


def test_upstream_timeout_before_the_stream_starts_gives_504(
    chat_client: TestClient, install_upstream: InstallUpstream
) -> None:
    def slow(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("slow", request=request)

    install_upstream(slow)
    r = chat_client.post("/v1/chat/completions", headers=HEADERS, json=_body())
    assert r.status_code == 504
    assert r.json()["error"]["code"] == "upstream_timeout"
