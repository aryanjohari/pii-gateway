"""Correlation ID propagation on HTTP responses."""

from starlette.testclient import TestClient


def test_correlation_id_header_roundtrip(client: TestClient) -> None:
    r = client.get("/healthz", headers={"X-Correlation-ID": "abc-123"})
    assert r.status_code == 200
    assert r.headers.get("X-Correlation-ID") == "abc-123"
