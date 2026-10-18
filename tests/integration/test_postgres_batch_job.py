"""Postgres batch job against an in-file SQLite database (same SQLAlchemy async path)."""

import json
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from pii_gateway.jobs.postgres_batch_job import run_postgres_batch_job
from pii_gateway.policy_schema import BatchQueryDef, PostgresBatchConfig
from pii_gateway.state_store import load_postgres_since

BATCH_CONFIG = PostgresBatchConfig(
    enabled=True,
    query_name="export_users",
    queries={
        "export_users": BatchQueryDef(
            sql="SELECT id, email FROM users WHERE updated_at > :since ORDER BY id",
            params_from="last_run_cursor",
        )
    },
)


@pytest.fixture
async def engine(tmp_path: Path) -> AsyncIterator[AsyncEngine]:
    eng = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'source.sqlite'}")
    async with eng.begin() as conn:
        await conn.execute(text("CREATE TABLE users (id INT, email TEXT, updated_at TEXT)"))
    yield eng
    await eng.dispose()


async def _insert_user(engine: AsyncEngine, *, user_id: int, email: str, updated_at: str) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO users VALUES (:id, :email, :updated_at)"),
            {"id": user_id, "email": email, "updated_at": updated_at},
        )


def _cleaned_lines(tmp_path: Path) -> list[list[dict[str, object]]]:
    return [
        [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
        for path in sorted((tmp_path / "out" / "cleaned").rglob("*.jsonl"))
    ]


async def test_rows_are_redacted_and_cursor_advances(
    tmp_path: Path, make_job_app: Callable[..., FastAPI], engine: AsyncEngine
) -> None:
    await _insert_user(engine, user_id=1, email="alice@example.com", updated_at="2020-01-01")
    app = make_job_app(postgres_batch=BATCH_CONFIG, postgres_engine=engine)
    before = datetime.now(UTC)

    await run_postgres_batch_job(app)

    assert _cleaned_lines(tmp_path) == [[{"id": 1, "email": "<EMAIL_ADDRESS>"}]]
    assert load_postgres_since(tmp_path / "state") >= before


async def test_second_run_only_exports_rows_changed_since_the_cursor(
    tmp_path: Path, make_job_app: Callable[..., FastAPI], engine: AsyncEngine
) -> None:
    await _insert_user(engine, user_id=1, email="alice@example.com", updated_at="2020-01-01")
    app = make_job_app(postgres_batch=BATCH_CONFIG, postgres_engine=engine)
    await run_postgres_batch_job(app)

    # Newer than the cursor the first run just saved.
    await _insert_user(engine, user_id=2, email="bob@example.com", updated_at="2999-01-01")
    await run_postgres_batch_job(app)

    exported = [rows for rows in _cleaned_lines(tmp_path) if rows]
    assert sorted(len(rows) for rows in exported) == [1, 1]
    assert {row["id"] for rows in exported for row in rows} == {1, 2}


async def test_no_matching_rows_still_advances_cursor(
    tmp_path: Path, make_job_app: Callable[..., FastAPI], engine: AsyncEngine
) -> None:
    app = make_job_app(postgres_batch=BATCH_CONFIG, postgres_engine=engine)
    before = datetime.now(UTC)

    await run_postgres_batch_job(app)

    assert all(rows == [] for rows in _cleaned_lines(tmp_path))
    assert load_postgres_since(tmp_path / "state") >= before
