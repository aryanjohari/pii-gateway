"""Pytest fixtures."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import pytest
from starlette.testclient import TestClient

from fake_s3 import FakeS3
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


@pytest.fixture
def fake_s3(monkeypatch: pytest.MonkeyPatch) -> FakeS3:
    fake = FakeS3()

    class _Session:
        def client(self, service: str, **kwargs: Any) -> Any:
            fake.client_kwargs.append({"service": service, **kwargs})

            @asynccontextmanager
            async def _ctx() -> AsyncIterator[FakeS3]:
                yield fake

            return _ctx()

    monkeypatch.setattr("aioboto3.Session", _Session)
    return fake
