"""Fixtures that build the app state batch jobs read (no HTTP layer)."""

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

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
