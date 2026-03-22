"""Outbound storage: local volume or S3-compatible API."""

from pathlib import Path
from typing import Literal, Protocol

from pii_gateway.settings import Settings

StorageLayer = Literal["raw", "cleaned"]


class OutboundStorage(Protocol):
    async def write_artifact(
        self,
        layer: StorageLayer,
        relative_key: str,
        data: bytes,
        content_type: str,
    ) -> None: ...


def create_outbound_storage(settings: Settings) -> OutboundStorage:
    if settings.storage_backend == "local":
        from pii_gateway.storage.local_volume_backend import LocalVolumeBackend

        return LocalVolumeBackend(root=settings.storage_local_path)
    from pii_gateway.storage.s3_compatible_backend import S3CompatibleBackend

    if not settings.s3_bucket:
        raise ValueError("S3_BUCKET is required when STORAGE_BACKEND=s3")
    return S3CompatibleBackend(
        bucket=settings.s3_bucket,
        prefix=settings.s3_prefix or "",
        endpoint_url=settings.s3_endpoint_url,
        region=settings.aws_region,
        access_key=settings.aws_access_key_id,
        secret_key=settings.aws_secret_access_key,
    )


def ensure_state_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
