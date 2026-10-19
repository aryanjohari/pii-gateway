"""The one place the Presidio analyzer is built, shared by the app and the eval harness."""

from presidio_analyzer import AnalyzerEngine


def build_analyzer() -> AnalyzerEngine:
    """Build the analyzer once per process; the eval calls this too, so it scores what runs."""
    return AnalyzerEngine()
