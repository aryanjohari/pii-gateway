"""POST /v1/chat/completions against a fake upstream (httpx.MockTransport)."""

import json
import logging
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from starlette.testclient import TestClient

BASE_URL = "https://llm.test/v1"
GATEWAY_KEY = "test-key"
CALLER_KEY = "sk-caller-secret"
UPSTREAM_REPLY = {
    "id": "chatcmpl-1",
    "object": "chat.completion",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "Noted <PERSON>."}}],
}
EMAIL = "alice@example.com"
HEADERS = {"X-API-Key": GATEWAY_KEY, "Authorization": f"Bearer {CALLER_KEY}"}


def _payload(content: Any = f"Please email {EMAIL}") -> dict[str, Any]:
    return {"model": "gpt-test", "messages": [{"role": "user", "content": content}]}


@pytest.fixture
def upstream_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_UPSTREAM_BASE_URL", BASE_URL)


@pytest.fixture
def chat_client(upstream_env: None, client: TestClient) -> TestClient:
    return client


@pytest.fixture
def upstream_calls(chat_client: TestClient) -> list[httpx.Request]:
    """Replace the lifespan's upstream client with one that records calls, not the network."""
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json=UPSTREAM_REPLY)

    state = chat_client.app.state  # type: ignore[attr-defined]
    state.llm_client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url=state.llm_client.base_url
    )
    return calls


def test_upstream_receives_only_redacted_text_and_the_callers_key(
    chat_client: TestClient, upstream_calls: list[httpx.Request]
) -> None:
    r = chat_client.post("/v1/chat/completions", headers=HEADERS, json=_payload())
    assert r.status_code == 200
    assert r.json() == UPSTREAM_REPLY
    assert len(upstream_calls) == 1
    sent = upstream_calls[0]
    assert str(sent.url) == f"{BASE_URL}/chat/completions"
    body = json.loads(sent.content)
    assert EMAIL not in sent.content.decode()
    assert "<EMAIL_ADDRESS>" in body["messages"][0]["content"]
    assert body["model"] == "gpt-test"
    assert sent.headers["Authorization"] == f"Bearer {CALLER_KEY}"
    assert "x-api-key" not in sent.headers


def test_logs_carry_no_keys_or_message_text(
    chat_client: TestClient,
    upstream_calls: list[httpx.Request],
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)  # production level; Presidio's DEBUG logs echo text
    r = chat_client.post("/v1/chat/completions", headers=HEADERS, json=_payload())
    assert r.status_code == 200
    logged = " ".join(
        f"{record.getMessage()} {getattr(record, 'log_extra', '')}" for record in caplog.records
    )
    assert "chat_complete" in logged
    for secret in (CALLER_KEY, GATEWAY_KEY, EMAIL):
        assert secret not in logged


@pytest.mark.parametrize(
    "headers",
    [{"Authorization": f"Bearer {CALLER_KEY}"}, {**HEADERS, "X-API-Key": "wrong"}],
    ids=["missing_gateway_key", "wrong_gateway_key"],
)
def test_gateway_key_is_required(
    chat_client: TestClient, upstream_calls: list[httpx.Request], headers: dict[str, str]
) -> None:
    r = chat_client.post("/v1/chat/completions", headers=headers, json=_payload())
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"
    assert upstream_calls == []


def test_callers_upstream_key_is_required(
    chat_client: TestClient, upstream_calls: list[httpx.Request]
) -> None:
    r = chat_client.post(
        "/v1/chat/completions", headers={"X-API-Key": GATEWAY_KEY}, json=_payload()
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "missing_upstream_key"
    assert upstream_calls == []


@pytest.mark.parametrize(
    ("payload", "code"),
    [
        (_payload([{"type": "image_url", "image_url": {}}]), "unsupported_content_type"),
        ({**_payload(), "stream": True}, "streaming_not_supported"),
        ({**_payload(), "tools": []}, "unsupported_field"),
        ({"model": "m", "messages": []}, "invalid_request"),
    ],
    ids=["image_part", "stream", "undeclared_field", "empty_messages"],
)
def test_unsupported_requests_are_rejected_and_nothing_is_forwarded(
    chat_client: TestClient,
    upstream_calls: list[httpx.Request],
    payload: dict[str, Any],
    code: str,
) -> None:
    r = chat_client.post("/v1/chat/completions", headers=HEADERS, json=payload)
    assert r.status_code == 422
    error = r.json()["error"]
    assert error["code"] == code
    assert set(error) == {"message", "type", "param", "code"}
    assert upstream_calls == []


def test_non_json_body_is_rejected(
    chat_client: TestClient, upstream_calls: list[httpx.Request]
) -> None:
    r = chat_client.post("/v1/chat/completions", headers=HEADERS, content=b"not json")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_json"
    assert upstream_calls == []


def test_oversize_text_is_rejected(
    chat_client: TestClient, upstream_calls: list[httpx.Request]
) -> None:
    chat_client.app.state.settings.sanitize_max_chars = 10  # type: ignore[attr-defined]
    r = chat_client.post("/v1/chat/completions", headers=HEADERS, json=_payload("x" * 50))
    assert r.status_code == 413
    assert r.json()["error"]["code"] == "payload_too_large"
    assert upstream_calls == []


def test_unset_upstream_url_gives_503(client: TestClient) -> None:
    r = client.post("/v1/chat/completions", headers=HEADERS, json=_payload())
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "misconfigured"


def test_redaction_failure_fails_closed(
    chat_client: TestClient, upstream_calls: list[httpx.Request]
) -> None:
    def explode(**_: object) -> None:
        raise RuntimeError("analyzer down")

    chat_client.app.state.analyzer = SimpleNamespace(analyze=explode)  # type: ignore[attr-defined]
    r = chat_client.post("/v1/chat/completions", headers=HEADERS, json=_payload())
    assert r.status_code == 500
    assert r.json()["error"]["code"] == "internal_error"
    assert EMAIL not in r.text
    assert upstream_calls == []


def test_rate_limit_applies_to_the_chat_route(
    chat_client: TestClient, upstream_calls: list[httpx.Request]
) -> None:
    chat_client.app.state.sanitize_rate_allow = lambda key: False  # type: ignore[attr-defined]
    r = chat_client.post("/v1/chat/completions", headers=HEADERS, json=_payload())
    assert r.status_code == 429
    assert r.json()["error"]["code"] == "rate_limited"
    assert upstream_calls == []
