"""JSON array file ingest tests."""

from pathlib import Path

import pytest

from pii_gateway.connectors.batch_json_array import load_json_array_objects


@pytest.mark.asyncio
async def test_load_json_array_objects_ok(tmp_path: Path) -> None:
    p = tmp_path / "d.json"
    p.write_text('[{"a": 1}, {"b": 2}]', encoding="utf-8")
    rows = await load_json_array_objects(p, max_bytes=1024)
    assert rows == [{"a": 1}, {"b": 2}]


@pytest.mark.asyncio
async def test_load_json_array_objects_invalid_root(tmp_path: Path) -> None:
    p = tmp_path / "d.json"
    p.write_text('{"not": "array"}', encoding="utf-8")
    with pytest.raises(ValueError, match="json_root_not_array"):
        await load_json_array_objects(p, max_bytes=1024)
