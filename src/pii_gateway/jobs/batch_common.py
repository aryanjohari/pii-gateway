"""Shared batch job helpers (sanitized NDJSON artifacts)."""

import json
import uuid
from typing import Any

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

from pii_gateway.core.sanitize_structured import sanitize_structured_root
from pii_gateway.policy_schema import GatewayPolicy
from pii_gateway.storage.outbound_interface import OutboundStorage
from pii_gateway.storage.paths import artifact_relative_key


async def write_sanitized_rows_ndjson(
    storage: OutboundStorage,
    *,
    rows: list[dict[str, Any]],
    policy: GatewayPolicy,
    analyzer: AnalyzerEngine,
    anonymizer: AnonymizerEngine,
    source: str,
) -> str:
    """Persist one cleaned NDJSON artifact; returns correlation id used in the path."""
    out_id = str(uuid.uuid4())
    lines: list[str] = []
    for row in rows:
        cleaned = sanitize_structured_root(
            row,
            policy=policy,
            analyzer=analyzer,
            anonymizer=anonymizer,
        )
        lines.append(json.dumps(cleaned, default=str))
    blob = ("\n".join(lines) + "\n").encode("utf-8")
    rel = artifact_relative_key(source, out_id, "jsonl")
    await storage.write_artifact("cleaned", rel, blob, "application/x-ndjson")
    return out_id
