"""Relaying an upstream event stream to the caller."""

import httpx

from pii_gateway.api.chat_stream import relay_stream


class _RecordingStream(httpx.AsyncByteStream):
    def __init__(self, chunks: list[bytes], fail_after: int | None = None) -> None:
        self._chunks = chunks
        self._fail_after = fail_after
        self.closed = False

    async def __aiter__(self):  # type: ignore[no-untyped-def]
        for index, chunk in enumerate(self._chunks):
            if self._fail_after == index:
                raise httpx.ReadError("connection cut")
            yield chunk

    async def aclose(self) -> None:
        self.closed = True


def _response(stream: _RecordingStream) -> httpx.Response:
    return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=stream)


async def test_chunks_are_relayed_unchanged_and_the_upstream_is_closed() -> None:
    stream = _RecordingStream([b"data: one\n\n", b"data: [DONE]\n\n"])
    received = [chunk async for chunk in relay_stream(_response(stream), "llm.test", "cid")]
    assert received == [b"data: one\n\n", b"data: [DONE]\n\n"]
    assert stream.closed


async def test_caller_disconnect_closes_the_upstream_request() -> None:
    stream = _RecordingStream([b"data: one\n\n", b"data: two\n\n"])
    relay = relay_stream(_response(stream), "llm.test", "cid")
    assert await anext(relay) == b"data: one\n\n"
    assert not stream.closed
    await relay.aclose()  # what the server does when the caller goes away
    assert stream.closed


async def test_interruption_ends_with_an_error_frame_naming_only_the_upstream_host() -> None:
    stream = _RecordingStream([b"data: one\n\n", b"data: two\n\n"], fail_after=1)
    received = [chunk async for chunk in relay_stream(_response(stream), "llm.test", "cid")]
    assert received[0] == b"data: one\n\n"
    assert b"upstream_stream_interrupted" in received[1]
    assert b"llm.test" in received[1]
    assert received[1].startswith(b"data: {") and received[1].endswith(b"\n\n")
    assert stream.closed
