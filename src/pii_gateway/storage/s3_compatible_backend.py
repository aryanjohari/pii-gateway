"""S3-compatible outbound storage (MinIO, R2, AWS S3)."""

import aioboto3

from pii_gateway.storage.outbound_interface import StorageLayer


class S3CompatibleBackend:
    def __init__(
        self,
        *,
        bucket: str,
        prefix: str,
        endpoint_url: str | None,
        region: str,
        access_key: str | None,
        secret_key: str | None,
    ) -> None:
        self._bucket = bucket
        self._prefix = prefix.strip("/")
        self._endpoint_url = endpoint_url
        self._region = region
        self._access_key = access_key
        self._secret_key = secret_key
        self._session = aioboto3.Session()

    def _object_key(self, layer: StorageLayer, relative_key: str) -> str:
        rel = relative_key.lstrip("/")
        if self._prefix:
            return f"{self._prefix}/{layer}/{rel}"
        return f"{layer}/{rel}"

    async def write_artifact(
        self,
        layer: StorageLayer,
        relative_key: str,
        data: bytes,
        content_type: str,
    ) -> None:
        key = self._object_key(layer, relative_key)

        async def _put() -> None:
            kwargs: dict[str, str | bytes | None] = {
                "Bucket": self._bucket,
                "Key": key,
                "Body": data,
                "ContentType": content_type,
            }
            client_kw: dict[str, str | None] = {"region_name": self._region}
            if self._endpoint_url:
                client_kw["endpoint_url"] = self._endpoint_url
            if self._access_key and self._secret_key:
                client_kw["aws_access_key_id"] = self._access_key
                client_kw["aws_secret_access_key"] = self._secret_key
            async with self._session.client("s3", **client_kw) as client:
                await client.put_object(**kwargs)

        await _put()
