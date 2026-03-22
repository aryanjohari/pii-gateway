"""Poll inbox (local or S3) for CSV / JSON array files and write cleaned NDJSON."""

import logging
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI

from pii_gateway.connectors import s3_inbox
from pii_gateway.connectors.batch_csv_pandas import iter_csv_rows
from pii_gateway.connectors.batch_json_array import load_json_array_objects
from pii_gateway.jobs.batch_common import write_sanitized_rows_ndjson
from pii_gateway.logging_config import get_logger, log_event
from pii_gateway.state_store import (
    fingerprint_local_file,
    load_processed_index,
    save_processed_index,
)

logger = get_logger(__name__)


def _normalize_csv_row(row: dict[str, object]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in row.items():
        key = str(k)
        if v is None or (isinstance(v, float) and pd.isna(v)):
            out[key] = None
        else:
            out[key] = v
    return out


async def run_file_ingest_job(app: FastAPI) -> None:
    settings = app.state.settings
    policy = app.state.policy
    storage = app.state.storage

    ingest = policy.batch_file_ingest
    if ingest.mode == "local":
        await _process_local_inbox(app, Path(ingest.local_path))
        return

    bucket = ingest.s3_bucket or settings.inbox_s3_bucket
    if not bucket:
        log_event(
            logger,
            logging.WARNING,
            "file_ingest_s3_missing_bucket",
            adapter="batch_file",
            config_version=policy.config_version,
            error_code="missing_inbox_bucket",
        )
        return

    prefix = ingest.s3_prefix or settings.inbox_s3_prefix
    keys = await s3_inbox.list_object_keys(
        bucket=bucket,
        prefix=prefix,
        endpoint_url=settings.s3_endpoint_url,
        region=settings.aws_region,
        access_key=settings.aws_access_key_id,
        secret_key=settings.aws_secret_access_key,
    )
    idx = load_processed_index(settings.gateway_state_dir)
    for key in keys:
        lower = key.lower()
        if not (lower.endswith(".csv") or lower.endswith(".json")):
            continue
        index_key = f"s3:{bucket}:{key}"
        data = await s3_inbox.get_object_bytes(
            bucket=bucket,
            key=key,
            endpoint_url=settings.s3_endpoint_url,
            region=settings.aws_region,
            access_key=settings.aws_access_key_id,
            secret_key=settings.aws_secret_access_key,
        )
        if len(data) > settings.batch_csv_max_bytes:
            log_event(
                logger,
                logging.WARNING,
                "file_ingest_object_too_large",
                adapter="batch_file",
                config_version=policy.config_version,
                error_code="object_too_large",
                artifact_key=key.split("/")[-1],
            )
            continue
        fp: dict[str, int | str] = {"size": len(data)}
        if idx.get(index_key) == fp:
            continue
        with tempfile.NamedTemporaryFile(
            suffix=Path(key).suffix,
            delete=False,
        ) as tmp:
            tmp.write(data)
            tmp_path = Path(tmp.name)
        out_id: str = ""
        row_count = 0
        try:
            if lower.endswith(".csv"):
                rows_s3: list[dict[str, Any]] = []
                async for row in iter_csv_rows(
                    tmp_path,
                    max_bytes=settings.batch_csv_max_bytes,
                ):
                    rows_s3.append(_normalize_csv_row(row))
                row_count = len(rows_s3)
                out_id = await write_sanitized_rows_ndjson(
                    storage,
                    rows=rows_s3,
                    policy=policy,
                    analyzer=app.state.analyzer,
                    anonymizer=app.state.anonymizer,
                    source="batch_csv",
                )
            else:
                objs = await load_json_array_objects(
                    tmp_path,
                    max_bytes=settings.batch_csv_max_bytes,
                )
                row_count = len(objs)
                out_id = await write_sanitized_rows_ndjson(
                    storage,
                    rows=objs,
                    policy=policy,
                    analyzer=app.state.analyzer,
                    anonymizer=app.state.anonymizer,
                    source="batch_json",
                )
        finally:
            tmp_path.unlink(missing_ok=True)

        idx[index_key] = fp
        save_processed_index(settings.gateway_state_dir, idx)
        log_event(
            logger,
            logging.INFO,
            "file_ingest_s3_complete",
            adapter="batch_file",
            config_version=policy.config_version,
            row_count=row_count,
            artifact_key=out_id,
        )


async def _process_local_inbox(app: FastAPI, inbox_dir: Path) -> None:
    settings = app.state.settings
    policy = app.state.policy
    storage = app.state.storage
    if not inbox_dir.is_dir():
        return

    idx = load_processed_index(settings.gateway_state_dir)
    for path in sorted(inbox_dir.iterdir()):
        if not path.is_file():
            continue
        lower = path.suffix.lower()
        if lower not in {".csv", ".json"}:
            continue
        key = str(path.resolve())
        fp_dict = fingerprint_local_file(path)
        fp: dict[str, int | str] = {
            "mtime_ns": fp_dict["mtime_ns"],
            "size": fp_dict["size"],
        }
        if idx.get(key) == fp:
            continue

        row_count = 0
        try:
            if lower == ".csv":
                rows: list[dict[str, Any]] = []
                async for row in iter_csv_rows(
                    path,
                    max_bytes=settings.batch_csv_max_bytes,
                ):
                    rows.append(_normalize_csv_row(row))
                row_count = len(rows)
                out_id = await write_sanitized_rows_ndjson(
                    storage,
                    rows=rows,
                    policy=policy,
                    analyzer=app.state.analyzer,
                    anonymizer=app.state.anonymizer,
                    source="batch_csv",
                )
            else:
                objs = await load_json_array_objects(
                    path,
                    max_bytes=settings.batch_csv_max_bytes,
                )
                row_count = len(objs)
                out_id = await write_sanitized_rows_ndjson(
                    storage,
                    rows=objs,
                    policy=policy,
                    analyzer=app.state.analyzer,
                    anonymizer=app.state.anonymizer,
                    source="batch_json",
                )
        except (OSError, ValueError) as exc:
            log_event(
                logger,
                logging.ERROR,
                "file_ingest_failed",
                adapter="batch_file",
                config_version=policy.config_version,
                error_code=type(exc).__name__,
                artifact_key=path.name,
            )
            continue

        idx[key] = fp
        save_processed_index(settings.gateway_state_dir, idx)
        log_event(
            logger,
            logging.INFO,
            "file_ingest_local_complete",
            adapter="batch_file",
            config_version=policy.config_version,
            row_count=row_count,
            artifact_key=out_id,
        )
