"""CSV batch ingest via Pandas (chunked reads, bounded memory per chunk)."""

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pandas as pd


async def iter_csv_rows(
    path: Path,
    *,
    max_bytes: int,
    chunksize: int = 500,
) -> AsyncIterator[dict[str, object]]:
    if not path.is_file():
        raise FileNotFoundError(str(path))
    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError("csv_file_too_large")

    def open_reader() -> Any:
        return pd.read_csv(path, chunksize=chunksize, dtype=object, iterator=True)

    reader: Any = await asyncio.to_thread(open_reader)
    while True:

        def next_chunk() -> pd.DataFrame | None:
            try:
                return reader.get_chunk()
            except StopIteration:
                return None

        chunk = await asyncio.to_thread(next_chunk)
        if chunk is None:
            break
        for row in chunk.to_dict(orient="records"):
            yield row
