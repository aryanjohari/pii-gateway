"""The one place the Presidio analyzer is built, shared by the app and the eval harness."""

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

from pii_gateway.core.recognizers.nz_driver_licence import NzDriverLicenceRecognizer
from pii_gateway.core.recognizers.nz_ird import NzIrdRecognizer
from pii_gateway.core.recognizers.nz_nhi import NzNhiRecognizer

# Named explicitly because Presidio's default model changes between versions. The large model found
# every labelled name in the eval where the small one missed 2 of 31 (see eval/results.md).
SPACY_MODEL = "en_core_web_lg"


def build_analyzer() -> AnalyzerEngine:
    """Build the analyzer once per process; the eval calls this too, so it scores what runs.

    The NZ recognisers are registered always but only run for a policy that lists their entity
    names, or for a policy with no entity list (which runs every recogniser).
    """
    nlp_engine = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": SPACY_MODEL}],
        }
    ).create_engine()
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
    for recognizer in (NzNhiRecognizer(), NzIrdRecognizer(), NzDriverLicenceRecognizer()):
        analyzer.registry.add_recognizer(recognizer)
    return analyzer
