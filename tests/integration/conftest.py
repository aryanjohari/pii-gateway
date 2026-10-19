"""Fixtures that build the app state batch jobs read (no HTTP layer)."""

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from starlette.testclient import TestClient

from pii_gateway.policy_schema import BatchFileIngestConfig, GatewayPolicy, PostgresBatchConfig
from pii_gateway.settings import Settings
from pii_gateway.storage.local_volume_backend import LocalVolumeBackend


@pytest.fixture(scope="session")
def presidio_engines() -> tuple[AnalyzerEngine, AnonymizerEngine]:
    # Loading the NLP model takes seconds, so share one pair across the session.
    return AnalyzerEngine(), AnonymizerEngine()  # type: ignore[no-untyped-call]


@pytest.fixture
def make_job_app(
    tmp_path: Path, presidio_engines: tuple[AnalyzerEngine, AnonymizerEngine]
) -> Callable[..., FastAPI]:
    """Build the minimal ``app.state`` a job reads, backed by real settings, policy and storage."""
    analyzer, anonymizer = presidio_engines

    def _make(
        *,
        postgres_batch: PostgresBatchConfig | None = None,
        postgres_engine: object | None = None,
        batch_file_ingest: BatchFileIngestConfig | None = None,
    ) -> FastAPI:
        inbox = tmp_path / "inbox"
        inbox.mkdir(exist_ok=True)
        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
            gateway_state_dir=tmp_path / "state",
            storage_local_path=tmp_path / "out",
        )
        policy = GatewayPolicy(
            redaction_entities=["EMAIL_ADDRESS"],
            structured_field_rules={"email": "redact"},
            batch_file_ingest=batch_file_ingest
            or BatchFileIngestConfig(mode="local", local_path=inbox),
            postgres_batch=postgres_batch or PostgresBatchConfig(),
        )
        state = SimpleNamespace(
            settings=settings,
            policy=policy,
            storage=LocalVolumeBackend(root=settings.storage_local_path),
            analyzer=analyzer,
            anonymizer=anonymizer,
            postgres_engine=postgres_engine,
        )
        return SimpleNamespace(state=state)  # type: ignore[return-value]

    return _make


@pytest.fixture
def upstream_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_UPSTREAM_BASE_URL", "https://llm.test/v1")


@pytest.fixture
def chat_client(upstream_env: None, client: TestClient) -> TestClient:
    return client


@pytest.fixture
def install_upstream(
    chat_client: TestClient,
) -> Callable[[Callable[[httpx.Request], httpx.Response]], list[httpx.Request]]:
    """Replace the lifespan's upstream client with one that records calls, not the network."""

    def install(handler: Callable[[httpx.Request], httpx.Response]) -> list[httpx.Request]:
        calls: list[httpx.Request] = []

        def recording(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            return handler(request)

        state = chat_client.app.state  # type: ignore[attr-defined]
        state.llm_client = httpx.AsyncClient(
            transport=httpx.MockTransport(recording), base_url=state.llm_client.base_url
        )
        return calls

    return install
