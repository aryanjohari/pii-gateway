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
    ("action", "field", "inp", "expected"),
    [
        ("redact", "note", "secret", "<NOTE>"),
        ("tokenize", "note", "secret", "<NOTE>"),
        ("redact", "email", "x@y.com", "<EMAIL_ADDRESS>"),
        ("tokenize", "email", "x@y.com", "<EMAIL_ADDRESS>"),
        ("redact", "full_name", "Bob Smith", "<PERSON>"),
        ("mask", "note", "abcd", "a**d"),
        ("mask", "note", "ab", "**"),
    ],
)
def test_field_actions(
    engines: tuple[AnalyzerEngine, AnonymizerEngine],
    action: FieldRule,
    field: str,
    inp: str,
    expected: str,
) -> None:
    analyzer, anonymizer = engines
    policy = GatewayPolicy(structured_field_rules={field: action})
    out = sanitize_structured_value(
        field,
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
    assert "<EMAIL_ADDRESS>" in out


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
    assert out["outer"]["email"] == "<EMAIL_ADDRESS>"
    assert out["items"][0]["email"] == "<EMAIL_ADDRESS>"


def test_demo_json_fields_consistent(
    engines: tuple[AnalyzerEngine, AnonymizerEngine],
) -> None:
    """Declared email + full_name both use Presidio-style placeholders."""
    analyzer, anonymizer = engines
    policy = GatewayPolicy(
        structured_field_rules={"email": "redact", "full_name": "redact"},
        redaction_entities=["EMAIL_ADDRESS", "PERSON"],
    )
    out = sanitize_structured_root(
        {
            "email": "bob@example.com",
            "full_name": "Bob Smith",
            "note": "Follow up with alice@example.com",
        },
        policy=policy,
        analyzer=analyzer,
        anonymizer=anonymizer,
    )
    assert out["email"] == "<EMAIL_ADDRESS>"
    assert out["full_name"] == "<PERSON>"
    assert "alice@example.com" not in str(out["note"])
