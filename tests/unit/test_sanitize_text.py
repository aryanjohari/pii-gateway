"""Free-text sanitization."""

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

from pii_gateway.core.sanitize_text import sanitize_free_text


def test_sanitize_free_text_empty() -> None:
    a, n = AnalyzerEngine(), AnonymizerEngine()
    assert sanitize_free_text("", analyzer=a, anonymizer=n, entity_types=[]) == ""


def test_sanitize_free_text_redacts_email() -> None:
    a, n = AnalyzerEngine(), AnonymizerEngine()
    out = sanitize_free_text(
        "mail me at alice@example.com",
        analyzer=a,
        anonymizer=n,
        entity_types=["EMAIL_ADDRESS"],
    )
    assert "alice@example.com" not in out
