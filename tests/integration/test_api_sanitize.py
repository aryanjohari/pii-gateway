"""HTTP sanitize integration tests."""

from pathlib import Path

import pytest
from starlette.testclient import TestClient

from pii_gateway.main import create_app


def test_sanitize_returns_503_when_api_key_not_configured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DISABLE_SCHEDULER", "true")
    monkeypatch.delenv("SANITIZE_HTTP_API_KEY", raising=False)
    monkeypatch.setenv("STORAGE_LOCAL_PATH", str(tmp_path / "out"))
    monkeypatch.setenv("GATEWAY_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.delenv("PII_GATEWAY_CONFIG_PATH", raising=False)
    monkeypatch.delenv("POSTGRES_BATCH_DSN", raising=False)
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    monkeypatch.delenv("STORAGE_BACKEND", raising=False)
    with TestClient(create_app()) as app_client:
        r = app_client.post("/v1/sanitize", json={"text": "hello"})
    assert r.status_code == 503
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "misconfigured"


def test_healthz(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_sanitize_requires_api_key(client: TestClient) -> None:
    r = client.post("/v1/sanitize", json={"text": "hello"})
    assert r.status_code == 401
    body = r.json()
    assert body["ok"] is False


def test_sanitize_redacts_email(client: TestClient) -> None:
    r = client.post(
        "/v1/sanitize",
        headers={"X-API-Key": "test-key"},
        json={"text": "Contact alice@example.com today"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "correlation_id" in data
    assert "alice@example.com" not in data["result"]["text"]


def test_sanitize_structured(client: TestClient) -> None:
    r = client.post(
        "/v1/sanitize",
        headers={"X-API-Key": "test-key"},
        json={"structured": {"email": "bob@example.com", "note": "hi"}},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "bob@example.com" not in str(data["result"])
