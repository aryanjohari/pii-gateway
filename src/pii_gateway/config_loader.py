"""Load and merge mounted YAML/JSON policy with runtime defaults."""

import json
from pathlib import Path
from typing import Any

import yaml

from pii_gateway.policy_schema import GatewayPolicy
from pii_gateway.settings import Settings


def _read_policy_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        loaded: Any = yaml.safe_load(text)
    elif path.suffix.lower() == ".json":
        loaded = json.loads(text)
    else:
        raise ValueError(f"Unsupported policy file extension: {path.suffix}")
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError("Policy file root must be a mapping")
    return loaded


def load_gateway_policy(settings: Settings) -> GatewayPolicy:
    """Load policy from ``PII_GATEWAY_CONFIG_PATH`` or return defaults."""
    if settings.pii_gateway_config_path is None:
        return GatewayPolicy()
    path = settings.pii_gateway_config_path
    if not path.is_file():
        raise FileNotFoundError(f"Policy file not found: {path}")
    raw = _read_policy_file(path)
    return GatewayPolicy.model_validate(raw)
