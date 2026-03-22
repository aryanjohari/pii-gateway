"""List and download objects from S3-compatible inbox."""

from typing import Any

import aioboto3


async def list_object_keys(
    *,
    bucket: str,
    prefix: str,
    endpoint_url: str | None,
    region: str,
    access_key: str | None,
    secret_key: str | None,
) -> list[str]:
    session = aioboto3.Session()
    client_kw: dict[str, str | None] = {"region_name": region}
    if endpoint_url:
        client_kw["endpoint_url"] = endpoint_url
    if access_key and secret_key:
        client_kw["aws_access_key_id"] = access_key
        client_kw["aws_secret_access_key"] = secret_key
    keys: list[str] = []
    async with session.client("s3", **client_kw) as client:
        token: str | None = None
        while True:
            kw: dict[str, Any] = {"Bucket": bucket}
            if prefix:
                kw["Prefix"] = prefix
            if token:
                kw["ContinuationToken"] = token
            resp = await client.list_objects_v2(**kw)
            for item in resp.get("Contents", []) or []:
                k = item.get("Key")
                if isinstance(k, str) and not k.endswith("/"):
                    keys.append(k)
            if not resp.get("IsTruncated"):
                break
            token = resp.get("NextContinuationToken")
            if not token:
                break
    return keys


async def get_object_bytes(
    *,
    bucket: str,
    key: str,
    endpoint_url: str | None,
    region: str,
    access_key: str | None,
    secret_key: str | None,
) -> bytes:
    session = aioboto3.Session()
    client_kw: dict[str, str | None] = {"region_name": region}
    if endpoint_url:
        client_kw["endpoint_url"] = endpoint_url
    if access_key and secret_key:
        client_kw["aws_access_key_id"] = access_key
        client_kw["aws_secret_access_key"] = secret_key
    async with session.client("s3", **client_kw) as client:
        resp = await client.get_object(Bucket=bucket, Key=key)
        body = resp["Body"]
        data: bytes = await body.read()
        return data
