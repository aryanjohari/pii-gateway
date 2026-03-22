"""Postgres batch export job."""

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI

from pii_gateway.connectors.batch_postgres_sqlalchemy import (
    build_postgres_params,
    iter_postgres_rows,
)
from pii_gateway.jobs.batch_common import write_sanitized_rows_ndjson
from pii_gateway.logging_config import get_logger, log_event
from pii_gateway.state_store import load_postgres_since, save_postgres_cursor

logger = get_logger(__name__)


async def run_postgres_batch_job(app: FastAPI) -> None:
    settings = app.state.settings
    policy = app.state.policy

    if settings.batch_demo_fixture:
        demo_rows: list[dict[str, Any]] = [
            {
                "id": 1,
                "email": "alice@example.com",
                "full_name": "Alice Example",
                "note": "Reach me at 555-0100",
            }
        ]
        out_id = await write_sanitized_rows_ndjson(
            app.state.storage,
            rows=demo_rows,
            policy=policy,
            analyzer=app.state.analyzer,
            anonymizer=app.state.anonymizer,
            source="postgres",
        )
        save_postgres_cursor(settings.gateway_state_dir, datetime.now(UTC))
        log_event(
            logger,
            logging.INFO,
            "postgres_batch_demo_complete",
            adapter="postgres",
            config_version=policy.config_version,
            row_count=len(demo_rows),
            artifact_key=out_id,
        )
        return

    if not policy.postgres_batch.enabled:
        return

    engine = app.state.postgres_engine
    if engine is None:
        log_event(
            logger,
            logging.WARNING,
            "postgres_batch_skipped",
            adapter="postgres",
            config_version=policy.config_version,
            error_code="no_engine",
        )
        return

    qname = policy.postgres_batch.query_name
    qdef = policy.postgres_batch.queries.get(qname)
    if qdef is None:
        log_event(
            logger,
            logging.ERROR,
            "postgres_batch_missing_query",
            adapter="postgres",
            config_version=policy.config_version,
            error_code="missing_query",
        )
        return

    since = load_postgres_since(settings.gateway_state_dir)
    params = build_postgres_params(params_from=qdef.params_from, since=since)
    rows: list[dict[str, Any]] = []
    async for row in iter_postgres_rows(engine, sql=qdef.sql, params=params):
        rows.append(row)

    out_id = await write_sanitized_rows_ndjson(
        app.state.storage,
        rows=rows,
        policy=policy,
        analyzer=app.state.analyzer,
        anonymizer=app.state.anonymizer,
        source="postgres",
    )
    save_postgres_cursor(settings.gateway_state_dir, datetime.now(UTC))
    log_event(
        logger,
        logging.INFO,
        "postgres_batch_complete",
        adapter="postgres",
        config_version=policy.config_version,
        row_count=len(rows),
        artifact_key=out_id,
    )
