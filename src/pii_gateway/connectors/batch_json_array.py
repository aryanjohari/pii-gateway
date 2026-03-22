"""JSON array file ingest (root must be an array of objects)."""

import asyncio
import json
from pathlib import Path
from typing import Any


async def load_json_array_objects(path: Path, *, max_bytes: int) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(str(path))
    if path.stat().st_size > max_bytes:
        raise ValueError("json_file_too_large")

    def _load() -> list[dict[str, Any]]:
        raw_text = path.read_text(encoding="utf-8")
        data = json.loads(raw_text)
        if not isinstance(data, list):
            raise ValueError("json_root_not_array")
        out: list[dict[str, Any]] = []
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("json_item_not_object")
            out.append(item)
        return out

    try:
        return await asyncio.to_thread(_load)
    except json.JSONDecodeError as exc:
        raise ValueError("json_parse_error") from exc
