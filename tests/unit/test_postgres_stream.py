"""SQLAlchemy streaming helper."""

from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

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
