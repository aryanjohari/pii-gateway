"""Clinic worked example: the upstream model sees placeholders, not the patient's details."""

import json
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest
from starlette.testclient import TestClient

NZ_LLM_POLICY = Path(__file__).resolve().parents[2] / "config" / "examples" / "config.nz-llm.yaml"
HEADERS = {"X-API-Key": "test-key", "Authorization": "Bearer sk-caller-secret"}
REPLY = {"id": "chatcmpl-1", "object": "chat.completion", "choices": []}
InstallUpstream = Callable[[Callable[[httpx.Request], httpx.Response]], list[httpx.Request]]


def _forwarded_note(client: TestClient, install_upstream: InstallUpstream, note: str) -> str:
    calls = install_upstream(lambda request: httpx.Response(200, json=REPLY))
    r = client.post(
        "/v1/chat/completions",
        headers=HEADERS,
        json={"model": "m", "messages": [{"role": "user", "content": note}]},
    )
    assert r.status_code == 200
    assert len(calls) == 1
    forwarded: str = json.loads(calls[0].content)["messages"][0]["content"]
    return forwarded


@pytest.mark.parametrize("client", [NZ_LLM_POLICY], indirect=True)
def test_clinic_note_reaches_the_upstream_as_placeholders(
    chat_client: TestClient, install_upstream: InstallUpstream
) -> None:
    note = "Patient Jane Smith (NHI ZAC5361) rang from 021 123 4567 about her results."
    forwarded = _forwarded_note(chat_client, install_upstream, note)
    assert (
        forwarded == "Patient <PERSON> (NHI <NZ_NHI>) rang from <PHONE_NUMBER> about her results."
    )


@pytest.mark.parametrize("client", [NZ_LLM_POLICY], indirect=True)
def test_lookalike_numbers_that_fail_their_checksum_are_not_over_redacted(
    chat_client: TestClient, install_upstream: InstallUpstream
) -> None:
    note = "Internal ref 180743145 and order ZAC5360 are not patient identifiers."
    assert _forwarded_note(chat_client, install_upstream, note) == note
