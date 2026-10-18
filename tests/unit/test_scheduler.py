"""Scheduler wiring: which jobs get registered from settings and policy."""

from collections.abc import AsyncIterator, Callable
from types import SimpleNamespace

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI

from pii_gateway.jobs.scheduler import setup_scheduler, shutdown_scheduler
from pii_gateway.policy_schema import GatewayPolicy, PostgresBatchConfig
from pii_gateway.settings import Settings


@pytest.fixture
async def build_scheduler() -> AsyncIterator[Callable[..., AsyncIOScheduler]]:
    started: list[AsyncIOScheduler] = []

    def _build(
        *, cron: str | None = None, poll_seconds: int | None = None, postgres_enabled: bool = True
    ) -> AsyncIOScheduler:
        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
            postgres_batch_cron=cron,
            batch_file_poll_seconds=poll_seconds,
        )
        policy = GatewayPolicy(postgres_batch=PostgresBatchConfig(enabled=postgres_enabled))
        app: FastAPI = SimpleNamespace(  # type: ignore[assignment]
            state=SimpleNamespace(settings=settings, policy=policy)
        )
        scheduler = setup_scheduler(app)
        started.append(scheduler)
        return scheduler

    yield _build
    for scheduler in started:
        shutdown_scheduler(scheduler)


async def test_cron_and_poll_settings_register_both_jobs(
    build_scheduler: Callable[..., AsyncIOScheduler],
) -> None:
    scheduler = build_scheduler(cron="0 3 * * *", poll_seconds=120)

    postgres_job = scheduler.get_job("postgres_batch")
    file_job = scheduler.get_job("file_ingest")
    assert postgres_job is not None and file_job is not None
    assert str(postgres_job.trigger) == str(CronTrigger.from_crontab("0 3 * * *"))
    assert file_job.trigger.interval.total_seconds() == 120


async def test_invalid_cron_skips_postgres_job_but_keeps_file_ingest(
    build_scheduler: Callable[..., AsyncIOScheduler],
) -> None:
    scheduler = build_scheduler(cron="not a cron")

    assert scheduler.get_job("postgres_batch") is None
    assert scheduler.get_job("file_ingest") is not None


async def test_cron_is_ignored_when_policy_disables_postgres_batch(
    build_scheduler: Callable[..., AsyncIOScheduler],
) -> None:
    scheduler = build_scheduler(cron="0 3 * * *", postgres_enabled=False)

    assert scheduler.get_job("postgres_batch") is None


async def test_poll_interval_is_clamped_to_five_seconds(
    build_scheduler: Callable[..., AsyncIOScheduler],
) -> None:
    scheduler = build_scheduler(poll_seconds=1)

    file_job = scheduler.get_job("file_ingest")
    assert file_job is not None
    assert file_job.trigger.interval.total_seconds() == 5
