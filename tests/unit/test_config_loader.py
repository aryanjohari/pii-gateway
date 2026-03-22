"""Policy loading tests."""

from pathlib import Path

import pytest

from pii_gateway.config_loader import load_gateway_policy
from pii_gateway.settings import Settings


def test_load_policy_missing_file(tmp_path: Path) -> None:
    settings = Settings.model_construct(pii_gateway_config_path=tmp_path / "nope.yaml")
    with pytest.raises(FileNotFoundError):
        load_gateway_policy(settings)


def test_load_policy_yaml_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "p.yaml"
    p.write_text(
        """
config_version: 2
redaction_entities: [EMAIL_ADDRESS]
structured_field_rules:
  email: redact
postgres_batch:
  enabled: false
  query_name: q
  queries: {}
batch_file_ingest:
  mode: local
  local_path: /tmp/inbox
  poll_seconds: 30
persistence:
  write_raw: false
  write_cleaned: true
""",
        encoding="utf-8",
    )
    settings = Settings.model_construct(pii_gateway_config_path=p)
    pol = load_gateway_policy(settings)
    assert pol.config_version == 2
    assert pol.structured_field_rules["email"] == "redact"


def test_default_policy_when_no_path() -> None:
    settings = Settings.model_construct(pii_gateway_config_path=None)
    pol = load_gateway_policy(settings)
    assert pol.config_version == 1
