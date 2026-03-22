"""Free-text sanitization via Presidio (no logging of input)."""

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine


def sanitize_free_text(
    text: str,
    *,
    analyzer: AnalyzerEngine,
    anonymizer: AnonymizerEngine,
    entity_types: list[str],
) -> str:
    if not text:
        return text
    entities = entity_types if entity_types else None
    results = analyzer.analyze(text=text, language="en", entities=entities)
    out = anonymizer.anonymize(text=text, analyzer_results=results)  # type: ignore[arg-type]
    return out.text
