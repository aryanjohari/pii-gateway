"""Supported subset of the OpenAI chat-completions request.

Anything outside the subset is rejected, never forwarded, so no unscanned
text reaches the upstream. Each rejection carries a stable error type that the
route can map to an API code.
"""

from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    model_validator,
)
from pydantic_core import PydanticCustomError


class _StrictModel(BaseModel):
    """Rejects undeclared fields by name; input values are hidden from error text."""

    model_config = ConfigDict(hide_input_in_errors=True)

    @model_validator(mode="before")
    @classmethod
    def reject_undeclared_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        undeclared = sorted(set(data) - set(cls.model_fields))
        if undeclared:
            raise PydanticCustomError(
                "unsupported_field",
                "Unsupported field(s): {names}",
                {"names": ", ".join(undeclared)},
            )
        return data


class TextPart(_StrictModel):
    type: Literal["text"]
    text: str


def _require_text_parts(content: Any) -> Any:
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") != "text":
                raise PydanticCustomError(
                    "unsupported_content_type",
                    "Only text content parts are supported",
                )
    return content


MessageContent = Annotated[
    str | Annotated[list[TextPart], Field(min_length=1)],
    BeforeValidator(_require_text_parts),
]


class ChatMessage(_StrictModel):
    role: Literal["system", "developer", "user", "assistant"]
    content: MessageContent


class ToolMessage(_StrictModel):
    role: Literal["tool"]
    content: MessageContent
    tool_call_id: str


class ChatCompletionRequest(_StrictModel):
    model: str = Field(min_length=1)
    messages: list[Annotated[ChatMessage | ToolMessage, Field(discriminator="role")]] = Field(
        min_length=1
    )
    stream: bool = False
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    max_completion_tokens: int | None = None
    n: int | None = None

    @model_validator(mode="after")
    def reject_streaming(self) -> "ChatCompletionRequest":
        if self.stream:
            raise PydanticCustomError(
                "streaming_not_supported",
                "stream=true is not supported yet",
            )
        return self
