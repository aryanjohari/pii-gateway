"""HTTP sanitize integration tests."""

from starlette.testclient import TestClient


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
