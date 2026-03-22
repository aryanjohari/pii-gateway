"""Pydantic v2 HTTP schemas."""

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ErrorDetail(BaseModel):
    code: str
    message: str


class SanitizeErrorResponse(BaseModel):
    ok: Literal[False] = False
    error: ErrorDetail


class SanitizeRequest(BaseModel):
    text: str | None = None
    structured: dict[str, Any] | None = None

    @model_validator(mode="after")
    def require_payload(self) -> "SanitizeRequest":
        if self.text is None and self.structured is None:
            raise ValueError("Provide at least one of text or structured")
        return self


class SanitizeSuccessResponse(BaseModel):
    ok: Literal[True] = True
    correlation_id: str
    adapter: str
    config_version: int
    result: dict[str, Any]
    meta: dict[str, Any] = Field(default_factory=dict)
