import pytest
from presidio_analyzer import AnalyzerEngine

from pii_gateway.core.analyzer_factory import SPACY_MODEL, build_analyzer


@pytest.fixture(scope="module")
def analyzer() -> AnalyzerEngine:
    return build_analyzer()  # loading the NLP model takes seconds, so share one


def test_analyzer_loads_the_pinned_spacy_model(analyzer: AnalyzerEngine) -> None:
    meta = analyzer.nlp_engine.nlp["en"].meta  # type: ignore[attr-defined]
    assert f"{meta['lang']}_{meta['name']}" == SPACY_MODEL


def _top_score(analyzer: AnalyzerEngine, text: str, entity: str) -> float:
    (result,) = analyzer.analyze(text=text, language="en", entities=[entity])
    return result.score


def test_built_analyzer_supports_default_and_nz_entities(analyzer: AnalyzerEngine) -> None:
    supported = set(analyzer.get_supported_entities(language="en"))
    assert {"EMAIL_ADDRESS", "PERSON", "PHONE_NUMBER"} <= supported
    assert {"NZ_NHI", "NZ_IRD", "NZ_DRIVER_LICENCE"} <= supported


@pytest.mark.parametrize(
    ("entity", "bare", "with_context"),
    [
        ("NZ_NHI", "ZAC5361", "Patient NHI ZAC5361"),
        ("NZ_IRD", "180743146", "Payroll IRD number 180743146"),
        ("NZ_DRIVER_LICENCE", "AB123456", "Driver licence AB123456"),
    ],
)
def test_nearby_context_words_raise_the_score(
    analyzer: AnalyzerEngine, entity: str, bare: str, with_context: str
) -> None:
    assert _top_score(analyzer, with_context, entity) > _top_score(analyzer, bare, entity)
