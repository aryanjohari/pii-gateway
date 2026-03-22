"""Structured sanitization branches (Presidio-backed)."""

from typing import Any, Literal

import pytest
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

from pii_gateway.core.sanitize_structured import sanitize_structured_root, sanitize_structured_value
from pii_gateway.policy_schema import GatewayPolicy

FieldRule = Literal["redact", "tokenize", "mask", "passthrough"]


@pytest.fixture(scope="module")
def engines() -> tuple[AnalyzerEngine, AnonymizerEngine]:
    return AnalyzerEngine(), AnonymizerEngine()


@pytest.mark.parametrize(
    ("action", "inp", "expected"),
    [
        ("redact", "secret", "<REDACTED>"),
        ("tokenize", "secret", "<NOTE_TOKEN>"),
        ("mask", "abcd", "a**d"),
        ("mask", "ab", "**"),
    ],
)
def test_field_actions(
    engines: tuple[AnalyzerEngine, AnonymizerEngine],
    action: FieldRule,
    inp: str,
    expected: str,
) -> None:
    analyzer, anonymizer = engines
    policy = GatewayPolicy(structured_field_rules={"note": action})
    out = sanitize_structured_value(
        "note",
        inp,
        policy=policy,
        analyzer=analyzer,
        anonymizer=anonymizer,
    )
    assert isinstance(out, str)
    assert out == expected


def test_passthrough_presidio_value(
    engines: tuple[AnalyzerEngine, AnonymizerEngine],
) -> None:
    analyzer, anonymizer = engines
    policy = GatewayPolicy(
        structured_field_rules={"note": "passthrough"},
        redaction_entities=["EMAIL_ADDRESS"],
    )
    out = sanitize_structured_value(
        "note",
        "Email me at jane.doe@example.com",
        policy=policy,
        analyzer=analyzer,
        anonymizer=anonymizer,
    )
    assert isinstance(out, str)
    assert "jane.doe@example.com" not in out


def test_nested_dict_and_list(engines: tuple[AnalyzerEngine, AnonymizerEngine]) -> None:
    analyzer, anonymizer = engines
    policy = GatewayPolicy(
        structured_field_rules={"email": "redact"},
        redaction_entities=[],
    )
    payload: dict[str, Any] = {
        "outer": {"email": "x@y.com"},
        "items": [{"email": "a@b.com"}, "plain"],
    }
    out = sanitize_structured_root(
        payload,
        policy=policy,
        analyzer=analyzer,
        anonymizer=anonymizer,
    )
    assert out["outer"]["email"] == "<REDACTED>"
    assert out["items"][0]["email"] == "<REDACTED>"
