"""Unit tests for artifact path helpers."""

from datetime import UTC, datetime

from pii_gateway.storage.paths import artifact_relative_key


def test_artifact_relative_key_shape() -> None:
    when = datetime(2026, 3, 22, tzinfo=UTC)
    rel = artifact_relative_key("http", "cid-1", "json", when=when)
    assert rel == "http/2026/03/22/cid-1.json"


def test_artifact_strips_traversal_segments() -> None:
    when = datetime(2026, 1, 2, tzinfo=UTC)
    rel = artifact_relative_key("..evil", "x", "txt", when=when)
    assert ".." not in rel
