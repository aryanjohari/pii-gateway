"""
Structured stdout logging (12-factor).

Allowed log context: event, correlation_id, adapter, config_version, duration_ms,
row_count, artifact_key (non-sensitive path segments), error_code, http_status.

Forbidden: raw HTTP bodies, SQL row payloads, file contents, tokens, passwords.
"""

import json
import logging
import sys
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root.addHandler(handler)


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra = getattr(record, "log_extra", None)
        if isinstance(extra, Mapping):
            for k, v in extra.items():
                if k in payload:
                    continue
                payload[k] = v
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    **fields: Any,
) -> None:
    """Emit one structured log line; ``fields`` must be safe (no PII)."""
    safe: dict[str, Any] = {"event": event, **fields}
    logger.log(level, event, extra={"log_extra": safe})


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
