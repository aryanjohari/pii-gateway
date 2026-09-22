"""Structured payload sanitization: field rules + Presidio on remaining strings."""

from collections.abc import Mapping
from typing import Any, Literal, cast

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

from pii_gateway.core.sanitize_text import sanitize_free_text
from pii_gateway.policy_schema import GatewayPolicy

FieldAction = Literal["redact", "tokenize", "mask", "passthrough"]

# Map common declared field names to Presidio entity types so field-rule
# placeholders match free-text anonymizer output (e.g. <EMAIL_ADDRESS>).
_FIELD_TO_ENTITY: dict[str, str] = {
    "email": "EMAIL_ADDRESS",
    "email_address": "EMAIL_ADDRESS",
    "full_name": "PERSON",
    "name": "PERSON",
    "person": "PERSON",
    "phone": "PHONE_NUMBER",
    "phone_number": "PHONE_NUMBER",
}


def _entity_placeholder(field: str) -> str:
    entity = _FIELD_TO_ENTITY.get(field.lower(), field.upper())
    return f"<{entity}>"


def _apply_field_action(value: str, field: str, action: FieldAction) -> str:
    if action == "redact":
        return _entity_placeholder(field)
    if action == "tokenize":
        # Same Presidio-style placeholder as redact; not cryptographic or reversible.
        return _entity_placeholder(field)
    if action == "mask":
        if len(value) <= 2:
            return "**"
        return value[0] + "*" * (len(value) - 2) + value[-1]
    return value


def sanitize_structured_value(
    field_key: str,
    value: Any,
    *,
    policy: GatewayPolicy,
    analyzer: AnalyzerEngine,
    anonymizer: AnonymizerEngine,
) -> Any:
    if isinstance(value, Mapping):
        m = cast(Mapping[str, Any], value)
        return {
            k: sanitize_structured_value(
                k,
                v,
                policy=policy,
                analyzer=analyzer,
                anonymizer=anonymizer,
            )
            for k, v in m.items()
        }
    if isinstance(value, list):
        out: list[Any] = []
        for item in value:
            if isinstance(item, Mapping):
                out.append(
                    sanitize_structured_root(
                        cast(Mapping[str, Any], item),
                        policy=policy,
                        analyzer=analyzer,
                        anonymizer=anonymizer,
                    )
                )
            else:
                out.append(
                    sanitize_structured_value(
                        field_key,
                        item,
                        policy=policy,
                        analyzer=analyzer,
                        anonymizer=anonymizer,
                    )
                )
        return out
    if not isinstance(value, str):
        return value

    rules = policy.structured_field_rules
    if field_key in rules:
        action = rules[field_key]
        updated = _apply_field_action(value, field_key, action)
        if action == "passthrough":
            return sanitize_free_text(
                updated,
                analyzer=analyzer,
                anonymizer=anonymizer,
                entity_types=policy.redaction_entities,
            )
        return updated

    return sanitize_free_text(
        value,
        analyzer=analyzer,
        anonymizer=anonymizer,
        entity_types=policy.redaction_entities,
    )


def sanitize_structured_root(
    data: Mapping[str, Any],
    *,
    policy: GatewayPolicy,
    analyzer: AnalyzerEngine,
    anonymizer: AnonymizerEngine,
) -> dict[str, Any]:
    return {
        k: sanitize_structured_value(
            k,
            v,
            policy=policy,
            analyzer=analyzer,
            anonymizer=anonymizer,
        )
        for k, v in data.items()
    }
