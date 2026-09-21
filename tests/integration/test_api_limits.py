"""Integration tests for sanitize rate limit and payload size."""

from pathlib import Path

import pytest
from starlette.testclient import TestClient

from pii_gateway.main import create_app


def _base_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISABLE_SCHEDULER", "true")
    monkeypatch.setenv("SANITIZE_HTTP_API_KEY", "test-key")
    monkeypatch.setenv("STORAGE_LOCAL_PATH", str(tmp_path / "out"))
    monkeypatch.setenv("GATEWAY_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.delenv("PII_GATEWAY_CONFIG_PATH", raising=False)
    monkeypatch.delenv("POSTGRES_BATCH_DSN", raising=False)
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    monkeypatch.delenv("STORAGE_BACKEND", raising=False)


def test_sanitize_rate_limited(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _base_env(tmp_path, monkeypatch)
    monkeypatch.setenv("SANITIZE_RATE_LIMIT_PER_MINUTE", "2")
    monkeypatch.setenv("SANITIZE_MAX_CHARS", "10000")
    headers = {"X-API-Key": "test-key"}
    with TestClient(create_app()) as client:
        assert client.post("/v1/sanitize", headers=headers, json={"text": "a"}).status_code == 200
        assert client.post("/v1/sanitize", headers=headers, json={"text": "b"}).status_code == 200
        r = client.post("/v1/sanitize", headers=headers, json={"text": "c"})
    assert r.status_code == 429
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "rate_limited"


def test_sanitize_rejects_oversize_chars(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _base_env(tmp_path, monkeypatch)
    monkeypatch.setenv("SANITIZE_RATE_LIMIT_PER_MINUTE", "0")
    monkeypatch.setenv("SANITIZE_MAX_CHARS", "20")
    with TestClient(create_app()) as client:
        r = client.post(
            "/v1/sanitize",
            headers={"X-API-Key": "test-key"},
            json={"text": "x" * 50},
        )
    assert r.status_code == 413
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "payload_too_large"


def test_sanitize_rejects_oversize_content_length(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _base_env(tmp_path, monkeypatch)
    monkeypatch.setenv("SANITIZE_RATE_LIMIT_PER_MINUTE", "0")
    monkeypatch.setenv("SANITIZE_MAX_BODY_BYTES", "32")
    monkeypatch.setenv("SANITIZE_MAX_CHARS", "0")
    payload = b'{"text":"' + (b"y" * 80) + b'"}'
    with TestClient(create_app()) as client:
        r = client.post(
            "/v1/sanitize",
            headers={
                "X-API-Key": "test-key",
                "Content-Type": "application/json",
                "Content-Length": str(len(payload)),
            },
            content=payload,
        )
    assert r.status_code == 413
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "payload_too_large"
