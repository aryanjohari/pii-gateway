"""Outbound storage factory."""

import pytest

from pii_gateway.settings import Settings
from pii_gateway.storage.local_volume_backend import LocalVolumeBackend
from pii_gateway.storage.outbound_interface import create_outbound_storage
from pii_gateway.storage.s3_compatible_backend import S3CompatibleBackend


def test_create_local_backend(tmp_path) -> None:
    s = Settings.model_construct(storage_backend="local", storage_local_path=tmp_path)
    backend = create_outbound_storage(s)
    assert isinstance(backend, LocalVolumeBackend)


def test_create_s3_requires_bucket(tmp_path) -> None:
    s = Settings.model_construct(
        storage_backend="s3",
        s3_bucket=None,
        aws_region="us-east-1",
    )
    with pytest.raises(ValueError, match="S3_BUCKET"):
        create_outbound_storage(s)


def test_create_s3_backend(tmp_path) -> None:
    s = Settings.model_construct(
        storage_backend="s3",
        s3_bucket="my-bucket",
        s3_prefix="pre",
        aws_region="us-east-1",
        s3_endpoint_url="http://localhost:9000",
        aws_access_key_id="k",
        aws_secret_access_key="s",
    )
    backend = create_outbound_storage(s)
    assert isinstance(backend, S3CompatibleBackend)
