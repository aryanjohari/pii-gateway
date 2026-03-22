"""Internal job triggers."""

from pathlib import Path

import pytest
import yaml
from starlette.testclient import TestClient

from pii_gateway.main import create_app


def test_internal_postgres_batch_demo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        yaml.safe_dump(
            {
                "config_version": 1,
                "redaction_entities": ["EMAIL_ADDRESS"],
                "structured_field_rules": {"email": "redact"},
                "postgres_batch": {"enabled": False, "query_name": "", "queries": {}},
                "batch_file_ingest": {
                    "mode": "local",
                    "local_path": str(inbox),
                    "poll_seconds": 3600,
                },
                "persistence": {"write_raw": False, "write_cleaned": True},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("PII_GATEWAY_CONFIG_PATH", str(cfg))
    monkeypatch.setenv("BATCH_DEMO_FIXTURE", "true")
    monkeypatch.setenv("DISABLE_SCHEDULER", "true")
    monkeypatch.setenv("SANITIZE_HTTP_API_KEY", "test-key")
    monkeypatch.setenv("INTERNAL_JOB_API_KEY", "job-secret")
    monkeypatch.setenv("STORAGE_LOCAL_PATH", str(tmp_path / "out"))
    monkeypatch.setenv("GATEWAY_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.delenv("POSTGRES_BATCH_DSN", raising=False)

    with TestClient(create_app()) as client:
        r = client.post(
            "/internal/jobs/postgres-batch",
            headers={"X-Internal-Job-Key": "job-secret"},
        )
    assert r.status_code == 200
    out_root = tmp_path / "out"
    assert out_root.exists()
    cleaned = list((out_root / "cleaned").rglob("*.jsonl"))
    assert cleaned


def test_internal_file_ingest_csv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "users.csv").write_text("email,note\na@b.com,hello\n", encoding="utf-8")
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        yaml.safe_dump(
            {
                "config_version": 1,
                "redaction_entities": ["EMAIL_ADDRESS"],
                "structured_field_rules": {"email": "redact"},
                "postgres_batch": {"enabled": False, "query_name": "", "queries": {}},
                "batch_file_ingest": {
                    "mode": "local",
                    "local_path": str(inbox),
                    "poll_seconds": 3600,
                },
                "persistence": {"write_raw": False, "write_cleaned": True},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("PII_GATEWAY_CONFIG_PATH", str(cfg))
    monkeypatch.setenv("DISABLE_SCHEDULER", "true")
    monkeypatch.setenv("SANITIZE_HTTP_API_KEY", "test-key")
    monkeypatch.setenv("INTERNAL_JOB_API_KEY", "job-secret")
    monkeypatch.setenv("STORAGE_LOCAL_PATH", str(tmp_path / "out"))
    monkeypatch.setenv("GATEWAY_STATE_DIR", str(tmp_path / "state"))

    with TestClient(create_app()) as client:
        r = client.post(
            "/internal/jobs/file-ingest",
            headers={"X-Internal-Job-Key": "job-secret"},
        )
    assert r.status_code == 200
    cleaned = list((tmp_path / "out" / "cleaned").rglob("*.jsonl"))
    assert cleaned
    text = cleaned[0].read_text(encoding="utf-8")
    assert "a@b.com" not in text
