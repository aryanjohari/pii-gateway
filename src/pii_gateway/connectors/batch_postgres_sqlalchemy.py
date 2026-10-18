"""Postgres batch rows via SQLAlchemy async (parameterized SQL from policy only)."""

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def create_batch_engine(dsn: str, *, command_timeout_seconds: float) -> AsyncEngine:
    # asyncpg's command_timeout bounds each query, so a hung DB cannot stall the job forever.
    return create_async_engine(dsn, connect_args={"command_timeout": command_timeout_seconds})


async def iter_postgres_rows(
    engine: AsyncEngine,
    *,
    sql: str,
    params: dict[str, Any],
) -> AsyncIterator[dict[str, Any]]:
    async with engine.connect() as conn:
        stream = await conn.stream(text(sql), params)
        async for row in stream:
            yield dict(row._mapping)


def build_postgres_params(
    *,
    params_from: str | None,
    since: datetime,
) -> dict[str, Any]:
    if params_from == "last_run_cursor":
        return {"since": since}
    return {}
