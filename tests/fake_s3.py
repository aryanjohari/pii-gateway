"""In-memory stand-in for the aioboto3 client, patched in at the library boundary."""

from typing import Any


class FakeS3:
    """Records calls and serves objects like an S3 client; ``fail_with`` makes every call raise."""

    def __init__(self, *, page_size: int = 1000) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}
        self.page_size = page_size
        self.fail_with: Exception | None = None
        self.fail_get_keys: dict[str, Exception] = {}
        self.client_kwargs: list[dict[str, Any]] = []
        self.put_calls: list[dict[str, Any]] = []

    def _check(self) -> None:
        if self.fail_with is not None:
            raise self.fail_with

    async def list_objects_v2(self, **kw: Any) -> dict[str, Any]:
        self._check()
        keys = sorted(
            k
            for (bucket, k) in self.objects
            if bucket == kw["Bucket"] and k.startswith(kw.get("Prefix", ""))
        )
        start = int(kw.get("ContinuationToken", 0))
        page = keys[start : start + self.page_size]
        more = start + self.page_size < len(keys)
        resp: dict[str, Any] = {"Contents": [{"Key": k} for k in page], "IsTruncated": more}
        if more:
            resp["NextContinuationToken"] = str(start + self.page_size)
        return resp

    async def get_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:  # noqa: N803
        self._check()
        if Key in self.fail_get_keys:
            raise self.fail_get_keys[Key]
        data = self.objects[(Bucket, Key)]

        class _Body:
            async def read(self) -> bytes:
                return data

        return {"Body": _Body()}

    async def put_object(self, **kw: Any) -> None:
        self._check()
        self.put_calls.append(kw)
        self.objects[(kw["Bucket"], kw["Key"])] = kw["Body"]
