"""Logical artifact paths (no PII in segments)."""

from datetime import UTC, datetime


def artifact_relative_key(
    source: str,
    correlation_id: str,
    ext: str,
    when: datetime | None = None,
) -> str:
    """Return ``source/YYYY/MM/DD/{correlation_id}.ext`` (UTC)."""
    now = when or datetime.now(UTC)
    y = f"{now.year:04d}"
    m = f"{now.month:02d}"
    d = f"{now.day:02d}"
    safe_source = source.replace("..", "").strip("/\\")
    return f"{safe_source}/{y}/{m}/{d}/{correlation_id}.{ext}"
