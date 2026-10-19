"""The one place the Presidio analyzer is built, shared by the app and the eval harness."""

from presidio_analyzer import AnalyzerEngine

from pii_gateway.core.recognizers.nz_driver_licence import NzDriverLicenceRecognizer
from pii_gateway.core.recognizers.nz_ird import NzIrdRecognizer
from pii_gateway.core.recognizers.nz_nhi import NzNhiRecognizer


def build_analyzer() -> AnalyzerEngine:
    """Build the analyzer once per process; the eval calls this too, so it scores what runs.

    The NZ recognisers are registered always but only run for a policy that lists their entity
    names, or for a policy with no entity list (which runs every recogniser).
    """
    analyzer = AnalyzerEngine()
    for recognizer in (NzNhiRecognizer(), NzIrdRecognizer(), NzDriverLicenceRecognizer()):
        analyzer.registry.add_recognizer(recognizer)
    return analyzer
