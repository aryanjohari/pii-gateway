"""Format-neutral redaction of a list of strings."""

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

from pii_gateway.core.redact_texts import redact_texts
from pii_gateway.core.sanitize_text import sanitize_free_text

ANALYZER = AnalyzerEngine()
ANONYMIZER = AnonymizerEngine()
EMAIL_ONLY = ["EMAIL_ADDRESS"]


def _redact(texts: list[str]) -> tuple[list[str], dict[str, int]]:
    return redact_texts(texts, analyzer=ANALYZER, anonymizer=ANONYMIZER, entity_types=EMAIL_ONLY)


def test_empty_string_and_clean_text_are_untouched() -> None:
    cleaned, counts = _redact(["", "nothing sensitive here"])
    assert cleaned == ["", "nothing sensitive here"]
    assert counts == {}


def test_order_is_preserved_and_pii_is_replaced() -> None:
    cleaned, _ = _redact(["first", "mail alice@example.com", "last"])
    assert cleaned[0] == "first"
    assert "alice@example.com" not in cleaned[1]
    assert "<EMAIL_ADDRESS>" in cleaned[1]
    assert cleaned[2] == "last"


def test_counts_add_up_across_texts() -> None:
    _, counts = _redact(["a@example.com and b@example.com", "c@example.com"])
    assert counts == {"EMAIL_ADDRESS": 3}


def test_output_matches_the_single_text_sanitizer() -> None:
    text = "reach me at alice@example.com please"
    cleaned, _ = _redact([text])
    expected = sanitize_free_text(
        text, analyzer=ANALYZER, anonymizer=ANONYMIZER, entity_types=EMAIL_ONLY
    )
    assert cleaned == [expected]
