"""Apply the format-neutral redactor to OpenAI chat messages."""

from collections.abc import Iterator

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

from pii_gateway.api.chat_schemas import ChatMessage, ToolMessage
from pii_gateway.core.redact_texts import redact_texts

Message = ChatMessage | ToolMessage


def redact_chat_messages(
    messages: list[Message],
    *,
    analyzer: AnalyzerEngine,
    anonymizer: AnonymizerEngine,
    entity_types: list[str],
) -> tuple[list[Message], dict[str, int]]:
    """Return redacted copies of the messages and entity-type counts."""
    texts = [text for message in messages for text in message_texts(message)]
    cleaned, counts = redact_texts(
        texts, analyzer=analyzer, anonymizer=anonymizer, entity_types=entity_types
    )
    cleaned_iter = iter(cleaned)
    return [_with_texts(message, cleaned_iter) for message in messages], counts


def message_texts(message: Message) -> list[str]:
    if isinstance(message.content, str):
        return [message.content]
    return [part.text for part in message.content]


def _with_texts(message: Message, cleaned: Iterator[str]) -> Message:
    if isinstance(message.content, str):
        return message.model_copy(update={"content": next(cleaned)})
    parts = [part.model_copy(update={"text": next(cleaned)}) for part in message.content]
    return message.model_copy(update={"content": parts})
