"""Shared S3 client options: timeouts and error context."""

from collections.abc import Iterator
from contextlib import contextmanager

from botocore.config import Config
from botocore.exceptions import ConnectTimeoutError, ReadTimeoutError


def s3_client_config(*, connect_timeout: float, read_timeout: float) -> Config:
    # Without explicit timeouts botocore waits 60s per phase, which stalls a scheduled job.
    return Config(connect_timeout=connect_timeout, read_timeout=read_timeout)


@contextmanager
def s3_timeout_context(operation: str, *, bucket: str, key: str | None = None) -> Iterator[None]:
    """Re-raise botocore timeouts as ``TimeoutError`` naming the operation, bucket and key."""
    try:
        yield
    except (ConnectTimeoutError, ReadTimeoutError) as exc:
        target = f"bucket={bucket}" + (f" key={key}" if key else "")
        raise TimeoutError(f"S3 {operation} timed out: {target}") from exc
