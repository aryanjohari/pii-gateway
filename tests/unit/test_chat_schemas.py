"""Unit tests for the supported subset of the OpenAI chat-completions request."""

from typing import Any

import pytest
from pydantic import ValidationError

from pii_gateway.api.chat_schemas import ChatCompletionRequest


def _error_types(payload: dict[str, Any]) -> list[str]:
    with pytest.raises(ValidationError) as exc:
        ChatCompletionRequest.model_validate(payload)
    return [error["type"] for error in exc.value.errors()]


def test_valid_request_keeps_roles_and_string_content() -> None:
    request = ChatCompletionRequest.model_validate(
        {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Be brief."},
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
            ],
            "temperature": 0.2,
        }
    )
    assert [message.role for message in request.messages] == ["system", "user", "assistant"]
    assert request.messages[1].content == "Hello"


def test_list_form_content_with_text_parts_is_accepted() -> None:
    request = ChatCompletionRequest.model_validate(
        {
            "model": "m",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "first"},
                        {"type": "text", "text": "second"},
                    ],
                }
            ],
        }
    )
    content = request.messages[0].content
    assert isinstance(content, list)
    assert [part.text for part in content] == ["first", "second"]


def test_tool_role_message_is_accepted_with_its_call_id() -> None:
    request = ChatCompletionRequest.model_validate(
        {
            "model": "m",
            "messages": [{"role": "tool", "content": "result", "tool_call_id": "call_1"}],
        }
    )
    assert request.messages[0].role == "tool"


def test_image_part_is_rejected_with_a_stable_code() -> None:
    payload = {
        "model": "m",
        "messages": [
            {
                "role": "user",
                "content": [{"type": "image_url", "image_url": {"url": "https://x/y.png"}}],
            }
        ],
    }
    assert "unsupported_content_type" in _error_types(payload)


def test_empty_messages_are_rejected() -> None:
    assert "too_short" in _error_types({"model": "m", "messages": []})


@pytest.mark.parametrize(
    "payload",
    [
        {"model": "m", "messages": [{"role": "user", "content": "x"}], "tools": []},
        {"model": "m", "messages": [{"role": "user", "content": "x"}], "stop": ["a"]},
        {"model": "m", "messages": [{"role": "user", "content": "x", "name": "Jane"}]},
        {
            "model": "m",
            "messages": [{"role": "assistant", "content": "x", "tool_calls": []}],
        },
    ],
    ids=["tools", "stop", "message_name", "assistant_tool_calls"],
)
def test_undeclared_fields_are_rejected_not_forwarded(payload: dict[str, Any]) -> None:
    assert "unsupported_field" in _error_types(payload)


def test_streaming_and_its_options_are_accepted() -> None:
    request = ChatCompletionRequest.model_validate(
        {
            "model": "m",
            "messages": [{"role": "user", "content": "x"}],
            "stream": True,
            "stream_options": {"include_usage": True},
        }
    )
    assert request.stream is True


def test_unknown_stream_option_is_rejected() -> None:
    payload = {
        "model": "m",
        "messages": [{"role": "user", "content": "x"}],
        "stream": True,
        "stream_options": {"include_usage": True, "surprise": 1},
    }
    assert "unsupported_field" in _error_types(payload)


def test_error_text_does_not_echo_message_content() -> None:
    secret = "NHI ZAC5361 and 021 555 0100"
    payload = {
        "model": "m",
        "messages": [{"role": "user", "content": secret, "name": "Jane"}],
    }
    with pytest.raises(ValidationError) as exc:
        ChatCompletionRequest.model_validate(payload)
    assert secret not in str(exc.value)
