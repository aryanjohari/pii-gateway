"""Format-neutral redaction of a list of strings (no logging of input)."""

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

from pii_gateway.core.entity_summary import entity_type_counts


def redact_texts(
    texts: list[str],
    *,
    analyzer: AnalyzerEngine,
    anonymizer: AnonymizerEngine,
    entity_types: list[str],
) -> tuple[list[str], dict[str, int]]:
    """Return cleaned strings in the same order, plus entity-type counts.

    Analyses each string once and reuses the result for both the replacement and
    the counts, so the counts always describe what was actually redacted.
    """
    entities = entity_types if entity_types else None
    cleaned: list[str] = []
    counts: dict[str, int] = {}
    for text in texts:
        if not text:
            cleaned.append(text)
            continue
        found = analyzer.analyze(text=text, language="en", entities=entities)
        cleaned.append(
            anonymizer.anonymize(text=text, analyzer_results=found).text  # type: ignore[arg-type]
        )
        for entity_type, count in entity_type_counts(found).items():
            counts[entity_type] = counts.get(entity_type, 0) + count
    return cleaned, counts
