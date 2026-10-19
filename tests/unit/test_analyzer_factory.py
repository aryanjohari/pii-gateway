from pii_gateway.core.analyzer_factory import build_analyzer


def test_built_analyzer_supports_the_entities_the_gateway_relies_on() -> None:
    supported = set(build_analyzer().get_supported_entities(language="en"))
    assert {"EMAIL_ADDRESS", "PERSON", "PHONE_NUMBER"} <= supported
