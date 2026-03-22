"""CSV iterator tests."""

from pathlib import Path

import pytest

from pii_gateway.connectors.batch_csv_pandas import iter_csv_rows


@pytest.mark.asyncio
async def test_iter_csv_rows_reads_chunks(tmp_path: Path) -> None:
    p = tmp_path / "f.csv"
    p.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
    rows: list[dict[str, object]] = []
    async for row in iter_csv_rows(p, max_bytes=1024, chunksize=1):
        rows.append(row)
    assert rows == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]


@pytest.mark.asyncio
async def test_iter_csv_rows_rejects_oversized(tmp_path: Path) -> None:
    p = tmp_path / "big.csv"
    p.write_text("x\n", encoding="utf-8")
    with pytest.raises(ValueError, match="too_large"):
        async for _ in iter_csv_rows(p, max_bytes=0):
            pass
