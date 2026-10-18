"""S3 inbox connector against a faked aioboto3 client."""

import pytest
from botocore.exceptions import ClientError, ReadTimeoutError

from fake_s3 import FakeS3
from pii_gateway.connectors import s3_inbox

CONNECTION = {
    "endpoint_url": "http://minio:9000",
    "region": "us-east-1",
    "access_key": "ak",
    "secret_key": "sk",
    "connect_timeout": 3.0,
    "read_timeout": 30.0,
}


async def test_list_object_keys_follows_pages_and_skips_folder_markers(fake_s3: FakeS3) -> None:
    fake_s3.page_size = 2
    for key in ["in/a.csv", "in/b.csv", "in/c.json", "in/sub/", "other/x.csv"]:
        fake_s3.objects[("bucket", key)] = b""

    keys = await s3_inbox.list_object_keys(bucket="bucket", prefix="in/", **CONNECTION)

    assert keys == ["in/a.csv", "in/b.csv", "in/c.json"]
    assert fake_s3.client_kwargs[0]["endpoint_url"] == "http://minio:9000"
    assert fake_s3.client_kwargs[0]["aws_access_key_id"] == "ak"


async def test_get_object_bytes_returns_body(fake_s3: FakeS3) -> None:
    fake_s3.objects[("bucket", "in/a.csv")] = b"email\na@b.com\n"

    data = await s3_inbox.get_object_bytes(bucket="bucket", key="in/a.csv", **CONNECTION)

    assert data == b"email\na@b.com\n"


async def test_client_error_is_not_swallowed(fake_s3: FakeS3) -> None:
    fake_s3.fail_with = ClientError({"Error": {"Code": "AccessDenied"}}, "ListObjectsV2")

    with pytest.raises(ClientError, match="AccessDenied"):
        await s3_inbox.list_object_keys(bucket="bucket", prefix="", **CONNECTION)


async def test_clients_are_built_with_the_configured_timeouts(fake_s3: FakeS3) -> None:
    await s3_inbox.list_object_keys(bucket="bucket", prefix="", **CONNECTION)

    config = fake_s3.client_kwargs[0]["config"]
    assert (config.connect_timeout, config.read_timeout) == (3.0, 30.0)


async def test_read_timeout_names_the_operation_bucket_and_key(fake_s3: FakeS3) -> None:
    fake_s3.fail_with = ReadTimeoutError(endpoint_url="http://minio:9000")

    with pytest.raises(TimeoutError, match=r"get_object timed out: bucket=bucket key=in/a\.csv"):
        await s3_inbox.get_object_bytes(bucket="bucket", key="in/a.csv", **CONNECTION)
