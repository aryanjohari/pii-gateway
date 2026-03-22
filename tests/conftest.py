"""Pytest fixtures."""

from pathlib import Path

import pytest
from starlette.testclient import TestClient

from pii_gateway.main import create_app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    out = tmp_path / "out"
    state = tmp_path / "state"
    monkeypatch.setenv("DISABLE_SCHEDULER", "true")
    monkeypatch.setenv("SANITIZE_HTTP_API_KEY", "test-key")
    monkeypatch.setenv("STORAGE_LOCAL_PATH", str(out))
    monkeypatch.setenv("GATEWAY_STATE_DIR", str(state))
    monkeypatch.delenv("PII_GATEWAY_CONFIG_PATH", raising=False)
    monkeypatch.delenv("POSTGRES_BATCH_DSN", raising=False)
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    monkeypatch.delenv("STORAGE_BACKEND", raising=False)
    monkeypatch.setenv("INTERNAL_JOB_API_KEY", "job-secret")
    with TestClient(create_app()) as test_client:
        yield test_client
