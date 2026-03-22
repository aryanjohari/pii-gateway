"""In-process APScheduler wiring (cron + interval). External cron can call internal HTTP instead."""

import logging
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI

from pii_gateway.jobs.file_ingest import run_file_ingest_job
from pii_gateway.jobs.postgres_batch_job import run_postgres_batch_job
from pii_gateway.logging_config import get_logger, log_event

logger = get_logger(__name__)


def setup_scheduler(app: FastAPI) -> AsyncIOScheduler:
    settings = app.state.settings
    policy = app.state.policy
    sched = AsyncIOScheduler()

    if settings.postgres_batch_cron and policy.postgres_batch.enabled:
        cron_expr = settings.postgres_batch_cron.strip()
        try:
            trigger = CronTrigger.from_crontab(cron_expr)
        except ValueError:
            log_event(
                logger,
                logging.ERROR,
                "invalid_postgres_cron",
                adapter="scheduler",
                config_version=policy.config_version,
                error_code="invalid_cron",
            )
        else:
            sched.add_job(
                run_postgres_batch_job,
                trigger,
                args=[app],
                max_instances=1,
                coalesce=True,
                id="postgres_batch",
            )

    poll = settings.batch_file_poll_seconds
    if poll is None:
        poll = policy.batch_file_ingest.poll_seconds
    poll_seconds = max(int(poll), 5)

    sched.add_job(
        run_file_ingest_job,
        "interval",
        seconds=poll_seconds,
        args=[app],
        max_instances=1,
        coalesce=True,
        id="file_ingest",
    )

    sched.start()
    log_event(
        logger,
        logging.INFO,
        "scheduler_started",
        adapter="scheduler",
        config_version=policy.config_version,
        duration_ms=0,
    )
    return sched


def shutdown_scheduler(scheduler: Any) -> None:
    scheduler.shutdown(wait=False)
