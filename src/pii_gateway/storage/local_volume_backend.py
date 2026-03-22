"""Write artifacts under a local root (Docker volume / bind mount)."""

import asyncio
from pathlib import Path

from pii_gateway.storage.outbound_interface import StorageLayer


def _sync_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


class LocalVolumeBackend:
    def __init__(self, root: Path) -> None:
        self._root = root

    async def write_artifact(
        self,
        layer: StorageLayer,
        relative_key: str,
        data: bytes,
        content_type: str,
    ) -> None:
        _ = content_type
        path = self._root / layer / relative_key
        await asyncio.to_thread(_sync_write, path, data)
