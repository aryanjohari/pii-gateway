"""SQLAlchemy streaming helper."""

from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from pii_gateway.connectors import batch_postgres_sqlalchemy
from pii_gateway.connectors.batch_postgres_sqlalchemy import iter_postgres_rows


@pytest.mark.asyncio
async def test_iter_postgres_rows_sqlite_file(tmp_path: Path) -> None:
    db_path = tmp_path / "t.sqlite"
    eng = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    async with eng.begin() as conn:
        await conn.execute(text("CREATE TABLE t (id INT, email TEXT)"))
        await conn.execute(text("INSERT INTO t VALUES (1, 'a@b.com')"))
        await conn.execute(text("INSERT INTO t VALUES (2, 'c@d.com')"))

    rows: list[dict[str, object]] = []
    sql = "SELECT id, email FROM t WHERE id > :min_id"
    async for row in iter_postgres_rows(eng, sql=sql, params={"min_id": 0}):
        rows.append(row)
    await eng.dispose()
    assert len(rows) == 2


def test_batch_engine_sets_asyncpg_command_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_create_async_engine(dsn: str, **kwargs: Any) -> str:
        captured.update(dsn=dsn, **kwargs)
        return "engine"

    monkeypatch.setattr(batch_postgres_sqlalchemy, "create_async_engine", fake_create_async_engine)

    batch_postgres_sqlalchemy.create_batch_engine(
        "postgresql+asyncpg://h/db", command_timeout_seconds=7
    )

    assert captured["connect_args"] == {"command_timeout": 7}
