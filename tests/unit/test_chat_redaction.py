"""Walking OpenAI chat messages through the format-neutral redactor."""

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

from pii_gateway.api.chat_redaction import Message, redact_chat_messages
from pii_gateway.api.chat_schemas import ChatCompletionRequest, ToolMessage

ANALYZER = AnalyzerEngine()
ANONYMIZER = AnonymizerEngine()


def _request(messages: list[dict[str, object]]) -> ChatCompletionRequest:
    return ChatCompletionRequest.model_validate({"model": "m", "messages": messages})


def _redact(request: ChatCompletionRequest) -> tuple[list[Message], dict[str, int]]:
    return redact_chat_messages(
        request.messages,
        analyzer=ANALYZER,
        anonymizer=ANONYMIZER,
        entity_types=["EMAIL_ADDRESS"],
    )


def test_string_content_is_redacted_and_roles_are_preserved() -> None:
    request = _request(
        [
            {"role": "system", "content": "Be brief."},
            {"role": "user", "content": "I am alice@example.com"},
        ]
    )
    cleaned, counts = _redact(request)
    assert [message.role for message in cleaned] == ["system", "user"]
    assert cleaned[0].content == "Be brief."
    assert "alice@example.com" not in str(cleaned[1].content)
    assert counts == {"EMAIL_ADDRESS": 1}


def test_list_form_text_parts_are_each_redacted() -> None:
    request = _request(
        [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "clean"},
                    {"type": "text", "text": "bob@example.com"},
                ],
            }
        ]
    )
    cleaned, counts = _redact(request)
    parts = cleaned[0].content
    assert isinstance(parts, list)
    assert [part.text for part in parts] == ["clean", "<EMAIL_ADDRESS>"]
    assert counts == {"EMAIL_ADDRESS": 1}


def test_mixed_string_and_list_messages_each_get_their_own_redacted_text() -> None:
    request = _request(
        [
            {"role": "user", "content": "first a@example.com"},
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "second"},
                    {"type": "text", "text": "third b@example.com"},
                ],
            },
            {"role": "user", "content": "fourth"},
        ]
    )
    cleaned, counts = _redact(request)
    assert cleaned[0].content == "first <EMAIL_ADDRESS>"
    parts = cleaned[1].content
    assert isinstance(parts, list)
    assert [part.text for part in parts] == ["second", "third <EMAIL_ADDRESS>"]
    assert cleaned[2].content == "fourth"
    assert counts == {"EMAIL_ADDRESS": 2}


def test_tool_call_id_survives_and_input_is_not_mutated() -> None:
    request = _request([{"role": "tool", "content": "carol@example.com", "tool_call_id": "call_1"}])
    cleaned, _ = _redact(request)
    assert isinstance(cleaned[0], ToolMessage)
    assert cleaned[0].tool_call_id == "call_1"
    assert request.messages[0].content == "carol@example.com"
