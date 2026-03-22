"""Orchestrate text + structured sanitization for HTTP handlers."""

from typing import Any

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

from pii_gateway.core.entity_summary import entity_type_counts
from pii_gateway.core.sanitize_structured import sanitize_structured_root
from pii_gateway.core.sanitize_text import sanitize_free_text
from pii_gateway.policy_schema import GatewayPolicy


def sanitize_payload(
    *,
    text: str | None,
    structured: dict[str, Any] | None,
    policy: GatewayPolicy,
    analyzer: AnalyzerEngine,
    anonymizer: AnonymizerEngine,
) -> tuple[dict[str, Any], dict[str, int]]:
    """Return result dict and merged entity counts (no raw PII)."""
    summary: dict[str, int] = {}
    result: dict[str, Any] = {}

    if text is not None and text != "":
        entities = policy.redaction_entities if policy.redaction_entities else None
        found = analyzer.analyze(text=text, language="en", entities=entities)
        summary = {**summary, **entity_type_counts(found)}
        result["text"] = sanitize_free_text(
            text,
            analyzer=analyzer,
            anonymizer=anonymizer,
            entity_types=policy.redaction_entities,
        )
    elif text is not None:
        result["text"] = text

    if structured is not None:
        st_entities = policy.redaction_entities if policy.redaction_entities else None
        for chunk in _collect_strings(structured):
            if not chunk:
                continue
            found2 = analyzer.analyze(text=chunk, language="en", entities=st_entities)
            summary = _merge_counts(summary, entity_type_counts(found2))
        result["structured"] = sanitize_structured_root(
            structured,
            policy=policy,
            analyzer=analyzer,
            anonymizer=anonymizer,
        )

    return result, summary


def _collect_strings(obj: Any, out: list[str] | None = None) -> list[str]:
    if out is None:
        out = []
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _collect_strings(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _collect_strings(v, out)
    return out


def _merge_counts(a: dict[str, int], b: dict[str, int]) -> dict[str, int]:
    merged = dict(a)
    for k, v in b.items():
        merged[k] = merged.get(k, 0) + v
    return merged
