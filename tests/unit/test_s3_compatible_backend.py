"""S3 outbound backend against a faked aioboto3 client."""

import pytest
from botocore.exceptions import ClientError

from fake_s3 import FakeS3
from pii_gateway.storage.s3_compatible_backend import S3CompatibleBackend


def _backend(prefix: str = "gw/") -> S3CompatibleBackend:
    return S3CompatibleBackend(
        bucket="out-bucket",
        prefix=prefix,
        endpoint_url="http://minio:9000",
        region="us-east-1",
        access_key="ak",
        secret_key="sk",
    )


async def test_write_artifact_puts_object_under_prefix_and_layer(fake_s3: FakeS3) -> None:
    await _backend().write_artifact(
        "cleaned", "/2026/10/19/x.jsonl", b"{}\n", "application/x-ndjson"
    )

    assert fake_s3.put_calls == [
        {
            "Bucket": "out-bucket",
            "Key": "gw/cleaned/2026/10/19/x.jsonl",
            "Body": b"{}\n",
            "ContentType": "application/x-ndjson",
        }
    ]


async def test_write_artifact_without_prefix_starts_at_layer(fake_s3: FakeS3) -> None:
    await _backend(prefix="").write_artifact("raw", "x.jsonl", b"", "text/plain")

    assert fake_s3.put_calls[0]["Key"] == "raw/x.jsonl"


async def test_write_artifact_propagates_client_error(fake_s3: FakeS3) -> None:
    fake_s3.fail_with = ClientError({"Error": {"Code": "AccessDenied"}}, "PutObject")

    with pytest.raises(ClientError, match="AccessDenied"):
        await _backend().write_artifact("cleaned", "x.jsonl", b"", "text/plain")
